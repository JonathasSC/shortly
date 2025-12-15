import logging

import mercadopago
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View
from django.views.generic import TemplateView

from apps.billing.domain import Pricing
from apps.billing.dto import CheckoutPreferenceDTO
from apps.billing.models import Plan, UserSubscription, UserWallet, WalletTransaction
from apps.billing.services import MercadoPagoService

logger = logging.getLogger(__name__)


class BuyCoinsView(LoginRequiredMixin, View):
    pricing = Pricing()

    def get(self, request, credit_amount, *args, **kwargs):
        price = self.pricing.get_package_price(credit_amount)

        logger.info(
            f"[COMPRA INICIADA] User={request.user.id} Credits={credit_amount}")

        sdk = mercadopago.SDK(settings.MERCADO_PAGO_ACCESS_TOKEN)
        mp_service = MercadoPagoService(sdk)

        if not price:
            return redirect("payment_failure")

        logger.debug(
            f"[VALIDAÇÃO OK] User={request.user.id} Package={credit_amount} Price={price}")

        success_url = request.build_absolute_uri(
            reverse("payment_success")
        ).replace("http://", "https://")

        failure_url = request.build_absolute_uri(
            reverse("payment_failure")
        ).replace("http://", "https://")

        pending_url = request.build_absolute_uri(
            reverse("payment_pending")
        ).replace("http://", "https://")

        logger.debug(
            f"[BACK_URLS] Success={success_url} - Failure={failure_url}")

        notification_url = request.build_absolute_uri(
            reverse("mp_webhook")
        ).replace("http://", "https://")

        logger.info(notification_url)

        checkout_data = CheckoutPreferenceDTO(
            title=f"{credit_amount} Créditos",
            price=price,
            quantity=1,
            back_urls={
                "success": success_url,
                "failure": failure_url,
                "pending": pending_url,
            },
            auto_return="approved",
            metadata={
                "user_id": str(request.user.id),
                "type": "credits",
                "amount": credit_amount,
            },
            notification_url=notification_url
        )

        preference = mp_service.create_checkout_preference(checkout_data)

        logger.info(f"[PREFERENCE RESPONSE] {preference}")

        if preference.get("status") == 201 and \
           preference.get("response", {}).get("init_point"):

            init_point = preference["response"]["init_point"]
            logger.info(
                f"[CHECKOUT REDIRECT] User={request.user.id} RedirectTo={init_point}"
            )
            return redirect(init_point)

        logger.error(f"[ERRO MERCADO PAGO] Preferência inválida: {preference}")
        return HttpResponse("Erro ao criar preferência", status=400)


class SubscribePlanView(LoginRequiredMixin, View):
    def post(self, request, plan_id, *args, **kwargs):
        plan = get_object_or_404(Plan, id=plan_id)

        subscription = UserSubscription.objects.create(
            user=request.user,
            plan=plan,
            status=UserSubscription.Status.INACTIVE,
        )

        wallet = request.user.wallet
        wallet_transaction = WalletTransaction.objects.create(
            wallet=wallet,
            transaction_type=WalletTransaction.TransactionType.CREDIT,
            amount=plan.monthly_credits,
            source="Mercado Pago - Assinatura",
            external_reference=str(subscription.id),
        )

        sdk = mercadopago.SDK(settings.MERCADO_PAGO_ACCESS_TOKEN)
        mp_service = MercadoPagoService(sdk)

        success_url = request.build_absolute_uri(
            reverse("payment_success")
        ).replace("http://", "https://")

        failure_url = request.build_absolute_uri(
            reverse("payment_failure")
        ).replace("http://", "https://")

        pending_url = request.build_absolute_uri(
            reverse("payment_pending")
        ).replace("http://", "https://")

        checkout_data = CheckoutPreferenceDTO(
            title=f"Assinatura: {plan.name}",
            price=plan.price,
            quantity=1,
            back_urls={
                "success": success_url,
                "failure": failure_url,
                "pending": pending_url,
            },
            external_reference=str(subscription.id),
            metadata={
                "type": "subscription",
                "subscription_id": subscription.id,
                "transaction_id": wallet_transaction.id,
            },
        )

        preference = mp_service.create_checkout_preference(checkout_data)

        if preference.get("status") == 201 and \
           preference.get("response", {}).get("init_point"):

            init_point = preference["response"]["init_point"]
            logger.info(
                f"[CHECKOUT REDIRECT] User={request.user.id} RedirectTo={init_point}"
            )
            return redirect(init_point)

        logger.error(f"[ERRO MERCADO PAGO] Preferência inválida: {preference}")
        return HttpResponse("Erro ao criar preferência", status=400)


class WalletPageView(View):
    template_name = "billing/wallet.html"
    paginate_by = 5

    prices = {
        10: 5.99,
        20: 10.99,
        50: 24.99,
        100: 39.99,
    }

    def get_prices_with_value(self):
        return {
            amount: {
                "total_price": price,
                "price_per_coin": round(price / amount, 2),
            }
            for amount, price in self.prices.items()
        }

    def get(self, request, *args, **kwargs):
        logger.info(f"Usuário {request.user.id} acessou a página da carteira.")
        prices_info = self.get_prices_with_value()
        plans = Plan.objects.all().order_by("price")

        wallet, _ = UserWallet.objects.get_or_create(user=request.user)
        transactions = WalletTransaction.objects.filter(
            wallet=wallet).order_by("-created_at")

        paginator = Paginator(transactions, self.paginate_by)
        transactions_page = paginator.get_page(request.GET.get("page"))

        logger.debug(
            f"Usuário {request.user.id} possui {wallet.balance} coins e {transactions.count()} transações."
        )
        return render(
            request,
            self.template_name,
            {
                "prices": prices_info,
                "plans": plans,
                "wallet": wallet,
                "transactions": transactions_page,
            },
        )


class PaymentSuccessView(TemplateView):
    template_name = "billing/payment/success.html"

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class PaymentPendingView(TemplateView):
    template_name = "billing/payment/pending.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        payment_id = self.request.GET.get(
            "payment_id") or kwargs.get("payment_id") or ""
        ctx["payment_id"] = payment_id
        return ctx


class PaymentFailureView(TemplateView):
    template_name = "billing/payment/failure.html"

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class PaymentStatusAPI(View):
    def get(self, request, *args, **kwargs):
        payment_id = request.GET.get("payment_id")

        if not payment_id:
            return JsonResponse({"error": "payment_id_required"}, status=400)

        logger.info(
            f"[STATUS API] Consulta de status | payment_id={payment_id}")

        try:
            sdk = mercadopago.SDK(settings.MERCADO_PAGO_ACCESS_TOKEN)
            payment_info = sdk.payment().get(payment_id)
            response = payment_info.get("response", {})
        except Exception as e:
            logger.error(f"[STATUS API] Erro ao consultar MP: {e}")
            return JsonResponse({"status": "unknown"}, status=500)

        status = response.get("status")

        logger.info(f"[STATUS API] Status do MP retornou: {status}")

        if status == "approved":
            return JsonResponse({"status": "approved"})

        return JsonResponse({"status": status or "unknown"})
