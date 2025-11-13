import hashlib
import hmac
import json

import mercadopago
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from apps.billing.models import Plan, UserSubscription, UserWallet, WalletTransaction
from apps.billing.services import MercadoPagoService


class BuyCoinsView(LoginRequiredMixin, View):
    prices = {
        10: 5.99,
        20: 10.99,
        50: 24.99,
        100: 39.99,
    }

    def get(self, request, credit_amount, *args, **kwargs):
        sdk = mercadopago.SDK(settings.MERCADO_PAGO_ACCESS_TOKEN)
        mp_service = MercadoPagoService(sdk)

        if credit_amount not in self.prices:
            return redirect("payment_failure")

        success_url = request.build_absolute_uri(reverse("payment_success"))
        failure_url = request.build_absolute_uri(reverse("payment_failure"))

        preference = mp_service.create_checkout_preference(
            title=f"{credit_amount} Credit's",
            price=self.prices[credit_amount],
            quantity=1,
            back_url_success=success_url,
            back_url_failure=failure_url,
            metadata={
                "user_id": str(request.user.id),
                "type": "credits",
                "amount": credit_amount,
            }
        )

        if preference.get("status") == 201:
            return redirect(preference["response"]["init_point"])
        else:
            return HttpResponse("Erro ao criar preferência de pagamento", status=400)


class SubscribePlanView(LoginRequiredMixin, View):
    def get(self, request, plan_id, *args, **kwargs):
        try:
            sdk = mercadopago.SDK(settings.MERCADO_PAGO_ACCESS_TOKEN)
            mp_service = MercadoPagoService(sdk)
            plan = Plan.objects.get(id=plan_id)

        except Plan.DoesNotExist:
            return redirect("payment_failure")

        success_url = request.build_absolute_uri(reverse("payment_success"))
        failure_url = request.build_absolute_uri(reverse("payment_failure"))

        preference = mp_service.create_checkout_preference(
            title=f"Assinatura: {plan.name}",
            price=plan.price,
            quantity=1,
            back_url_success=success_url,
            back_url_failure=failure_url,
            metadata={
                "user_id": str(request.user.id),
                "type": "plan",
                "plan_id": plan.id
            }
        )

        return redirect(preference["response"]["init_point"])


@method_decorator(csrf_exempt, name='dispatch')
class MercadoPagoWebhookView(View):
    sdk = mercadopago.SDK(settings.MERCADO_PAGO_ACCESS_TOKEN)
    mp_service = MercadoPagoService(sdk)

    def _process_wallet_credit(self, user_id, amount, payment_id):
        try:
            User = get_user_model()
            User.objects.get(pk=user_id)
        except User.DoesNotExist:
            raise ValueError("user_not_found")

        try:
            amount = int(float(amount))
        except (TypeError, ValueError):
            return {"status": "invalid_amount"}

        if WalletTransaction.objects.filter(external_reference=payment_id).exists():
            return {"status": "already_processed"}

        wallet, _ = UserWallet.objects.get_or_create(user_id=user_id)

        with transaction.atomic():
            wallet.credit(amount)
            WalletTransaction.objects.create(
                wallet=wallet,
                amount=amount,
                transaction_type=WalletTransaction.TransactionType.CREDIT,
                source=f"Crédito de {amount} coins via Mercado Pago",
                external_reference=str(payment_id)
            )

        return {"status": "wallet_updated"}

    def _activate_subscription(self, user_id, plan_id):
        plan = Plan.objects.get(id=plan_id)
        UserSubscription.objects.update_or_create(
            user_id=user_id,
            defaults={"plan": plan, "is_active": True}
        )

    def _verify_signature(self, request):
        secret = settings.MERCADO_PAGO_WEBHOOK_SECRET

        x_signature = request.headers.get("X-Signature")
        x_request_id = request.headers.get("X-Request-Id")

        payment_id = (
            request.GET.get("id")
            or request.GET.get("data.id")
            or (json.loads(request.body.decode("utf-8")).get("data", {}) or {}).get("id")
        )

        if not x_signature or not payment_id:
            return False

        message = f"id:{payment_id};request-id:{x_request_id}".encode("utf-8")
        expected_hmac = hmac.new(
            secret.encode("utf-8"),
            message,
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(expected_hmac, x_signature)

    def post(self, request, *args, **kwargs):
        return self.handle_webhook(request)

    def get(self, request, *args, **kwargs):
        return self.handle_webhook(request)

    def handle_webhook(self, request):
        if not self._verify_signature(request):
            return JsonResponse({"error": "invalid_signature"}, status=403)

        if request.content_type == "application/json":
            try:
                data = json.loads(request.body.decode("utf-8"))
            except Exception:
                data = {}
        else:
            data = request.GET or request.POST

        topic = data.get("topic") or data.get("type")
        if topic != "payment":
            return JsonResponse({"status": "ignored"})

        payment_id = (
            data.get("id")
            or data.get("data.id")
            or (data.get("data", {}) or {}).get("id")
        )

        if not payment_id:
            return JsonResponse({"error": "id not found"}, status=400)

        try:
            payment_info = self.mp_service.sdk.payment().get(payment_id)
            payment_data = payment_info.get("response", {})
        except Exception as e:
            return JsonResponse({"error": f"failed to fetch payment: {str(e)}"}, status=500)

        if payment_data.get("status") != "approved":
            return JsonResponse({"status": "pending_or_failed"})

        metadata = payment_data.get("metadata", {})
        payment_type = metadata.get("type")
        user_id = metadata.get("user_id")

        if payment_type == "credits":
            try:
                result = self._process_wallet_credit(
                    user_id=user_id,
                    amount=metadata.get("amount"),
                    payment_id=payment_id
                )
                return JsonResponse(result)

            except ValueError as e:
                return JsonResponse({"error": str(e)}, status=400)

            except Exception:
                return JsonResponse({"error": "internal_error"}, status=500)

        if payment_type == "plan":
            self._activate_subscription(
                user_id=user_id,
                plan_id=metadata.get("plan_id")
            )
            return JsonResponse({"status": "subscription_activated"})

        return JsonResponse({"status": "ignored_no_valid_type"})


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
        prices_info = {}
        for amount, price in self.prices.items():
            price_per_coin = price / amount
            prices_info[amount] = {
                "total_price": price,
                "price_per_coin": round(price_per_coin, 2),
            }
        return prices_info

    def get(self, request, *args, **kwargs):
        prices_info = self.get_prices_with_value()
        plans = Plan.objects.all().order_by('price')

        wallet, _ = UserWallet.objects.get_or_create(
            user=request.user
        )

        transactions = WalletTransaction.objects.filter(
            wallet=wallet
        ).order_by("-created_at")

        paginator = Paginator(transactions, self.paginate_by)
        transactions_page = paginator.get_page(request.GET.get("page"))

        return render(request, self.template_name, {
            "prices": prices_info,
            "plans": plans,
            "wallet": wallet,
            "transactions": transactions_page
        })
