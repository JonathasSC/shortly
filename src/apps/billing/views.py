import mercadopago
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View

from apps.billing.models import Plan, UserSubscription, UserWallet, WalletTransaction
from apps.billing.services import MercadoPagoService


class BuyCoinsView(View):
    prices = {
        10: 5.99,
        20: 10.99,
        50: 24.99,
        100: 39.99,
    }

    def get(self, request, coin_amount, *args, **kwargs):
        sdk = mercadopago.SDK(settings.MERCADO_PAGO_ACCESS_TOKEN)
        mp_service = MercadoPagoService(sdk)

        if coin_amount not in self.prices:
            return redirect("payment_failure")

        success_url = request.build_absolute_uri(reverse("payment_success"))
        failure_url = request.build_absolute_uri(reverse("payment_failure"))

        preference = mp_service.create_checkout_preference(
            title=f"{coin_amount} Coins",
            price=self.prices[coin_amount],
            quantity=1,
            back_url_success=success_url,
            back_url_failure=failure_url,
            metadata={
                "user_id": str(request.user.id),
                "type": "coins",
                "amount": coin_amount,
            }
        )

        if preference.get("status") == 201:
            return redirect(preference["response"]["init_point"])
        else:
            print("ERRO NO RETORNO:", preference)
            return HttpResponse("Erro ao criar preferência de pagamento", status=400)


class SubscribePlanView(View):

    def get(self, request, plan_id, *args, **kwargs):
        try:
            sdk = mercadopago.SDK(settings.MERCADO_PAGO_ACCESS_TOKEN)
            mp_service = MercadoPagoService(sdk)
            plan = Plan.objects.get(id=plan_id)
            print(plan)
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


class MercadoPagoWebhookView(View):
    sdk = mercadopago.SDK(settings.MERCADO_PAGO_ACCESS_TOKEN)
    mp_service = MercadoPagoService(sdk)

    def post(self, request, *args, **kwargs):
        return self.handle_webhook(request)

    def get(self, request, *args, **kwargs):
        return self.handle_webhook(request)

    def handle_webhook(self, request):
        data = request.GET or request.POST
        topic = data.get("topic") or data.get("type")

        if topic != "payment":
            return JsonResponse({"status": "ignored"})

        payment_id = data.get("id") or data.get("data.id")
        if not payment_id:
            return JsonResponse({"error": "id not found"}, status=400)

        try:
            payment_info = self.mp_service.sdk.payment().get(payment_id)
            payment_data = payment_info.get("response", {})
        except Exception as e:
            return JsonResponse({"error": f"failed to fetch payment: {str(e)}"}, status=500)

        status = payment_data.get("status")
        metadata = payment_data.get("metadata", {})

        if status != "approved":
            return JsonResponse({"status": "pending_or_failed"})

        payment_type = metadata.get("type")
        user_id = metadata.get("user_id")

        if payment_type == "coins":
            amount = metadata.get("amount", 0)

            wallet, _ = UserWallet.objects.get_or_create(user_id=user_id)
            wallet.balance += int(amount)
            wallet.save()

            WalletTransaction.objects.create(
                user_id=user_id,
                amount=int(amount),
                transaction_type="CREDIT",
                description=f"Crédito de {amount} coins via Mercado Pago",
                external_reference=str(payment_id)
            )

            return JsonResponse({"status": "wallet_updated"})

        if payment_type == "plan":
            plan_id = metadata.get("plan_id")
            plan = Plan.objects.get(id=plan_id)

            UserSubscription.objects.update_or_create(
                user_id=user_id,
                defaults={
                    "plan": plan,
                    "is_active": True,
                }
            )

            return JsonResponse({"status": "subscription_activated"})

        return JsonResponse({"status": "ignored_no_valid_type"})


class WalletPageView(View):
    template_name = "billing/wallet.html"

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
        plans = Plan.objects.all()

        wallet, _ = UserWallet.objects.get_or_create(
            user=request.user
        )
        transactions = WalletTransaction.objects.filter(
            wallet=wallet
        ).order_by("-created_at")

        return render(request, self.template_name, {
            "prices": prices_info,
            "plans": plans,
            "wallet": wallet,
            "transactions": transactions
        })
