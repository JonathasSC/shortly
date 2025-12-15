import logging

import mercadopago
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View

from apps.billing.models import Plan, UserWallet, WalletTransaction
from apps.billing.services import MercadoPagoService

logger = logging.getLogger(__name__)


class BuyCoinsView(LoginRequiredMixin, View):
    prices = {
        10: 5.99,
        20: 10.99,
        50: 24.99,
        100: 39.99,
    }

    def get(self, request, credit_amount, *args, **kwargs):
        logger.info(
            f"Usuário {request.user.id} iniciou compra de {credit_amount} créditos.")

        sdk = mercadopago.SDK(settings.MERCADO_PAGO_ACCESS_TOKEN)
        mp_service = MercadoPagoService(sdk)

        if credit_amount not in self.prices:
            logger.warning(
                f"Tentativa de compra inválida de {credit_amount} créditos por {request.user.id}")
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
            logger.info(
                f"Preferência de pagamento criada com sucesso para {request.user.id}")
            return redirect(preference["response"]["init_point"])
        else:
            logger.error(
                f"Erro ao criar preferência de pagamento para {request.user.id}: {preference}")
            return HttpResponse("Erro ao criar preferência de pagamento", status=400)


class SubscribePlanView(LoginRequiredMixin, View):
    def get(self, request, plan_id, *args, **kwargs):
        try:
            sdk = mercadopago.SDK(settings.MERCADO_PAGO_ACCESS_TOKEN)
            mp_service = MercadoPagoService(sdk)
            plan = Plan.objects.get(id=plan_id)
            logger.info(
                f"Usuário {request.user.id} iniciou assinatura do plano {plan_id}")

        except Plan.DoesNotExist:
            logger.warning(
                f"Plano {plan_id} não encontrado para assinatura por {request.user.id}")
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

        logger.info(
            f"Preferência de pagamento criada para assinatura do plano {plan_id} pelo usuário {request.user.id}")
        return redirect(preference["response"]["init_point"])


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
        plans = Plan.objects.all().order_by('price')

        wallet, _ = UserWallet.objects.get_or_create(user=request.user)
        transactions = WalletTransaction.objects.filter(
            wallet=wallet).order_by("-created_at")

        paginator = Paginator(transactions, self.paginate_by)
        transactions_page = paginator.get_page(request.GET.get("page"))

        logger.debug(
            f"Usuário {request.user.id} possui {wallet.balance} coins e {transactions.count()} transações.")
        return render(request, self.template_name, {
            "prices": prices_info,
            "plans": plans,
            "wallet": wallet,
            "transactions": transactions_page
        })
