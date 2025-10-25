import mercadopago
from django.conf import settings
from django.core.paginator import EmptyPage, Paginator
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from apps.billing.models import Plan, UserSubscription, UserWallet, WalletTransaction
from apps.billing.services import MercadoPagoService
import json


class BuyCoinsView(View):
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


class SubscribePlanView(View):
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

    def _process_wallet_credit(user_id, amount, payment_id):
        print(
            f"[DEBUG] Iniciando crédito de carteira | user_id={user_id}, amount={amount}, payment_id={payment_id}")

        wallet, _ = UserWallet.objects.get_or_create(user_id=user_id)

        print(
            f"[DEBUG] Carteira localizada/criada: wallet_id={wallet.id}, saldo_atual={wallet.balance}")
        amount = int(float(amount))
        wallet.balance += int(amount)
        wallet.save()
        print(f"[DEBUG] Novo saldo da carteira: {wallet.balance}")

        WalletTransaction.objects.create(
            user_id=user_id,
            amount=int(amount),
            transaction_type="CREDIT",
            description=f"Crédito de {amount} coins via Mercado Pago",
            external_reference=str(payment_id)
        )
        print(
            f"[DEBUG] Transação de carteira registrada para user_id={user_id}")

    def _activate_subscription(user_id, plan_id):
        print(
            f"[DEBUG] Ativando assinatura | user_id={user_id}, plan_id={plan_id}")

        plan = Plan.objects.get(id=plan_id)
        print(
            f"[DEBUG] Plano localizado: {plan.name if hasattr(plan, 'name') else plan.id}")

        UserSubscription.objects.update_or_create(
            user_id=user_id,
            defaults={"plan": plan, "is_active": True}
        )
        print(
            f"[DEBUG] Assinatura ativada ou atualizada com sucesso para user_id={user_id}")

    def post(self, request, *args, **kwargs):
        print("[DEBUG] Webhook recebido via POST")
        return self.handle_webhook(request)

    def get(self, request, *args, **kwargs):
        print("[DEBUG] Webhook recebido via GET")
        return self.handle_webhook(request)

    def handle_webhook(self, request):
        if request.content_type == "application/json":
            try:
                data = json.loads(request.body.decode("utf-8"))
            except Exception:
                data = {}
            else:
                data = request.GET or request.POST

        topic = data.get("topic") or data.get("type")
        if topic != "payment":
            print("[DEBUG] Evento ignorado — não é um pagamento")
            return JsonResponse({"status": "ignored"})

        payment_id = (
            data.get("id")
            or data.get("data.id")
            or (data.get("data", {}) or {}).get("id")
        )
        print(f"[DEBUG] payment_id extraído: {payment_id}")

        if not payment_id:
            print("[DEBUG] ERRO: ID de pagamento não encontrado no payload")
            return JsonResponse({"error": "id not found"}, status=400)

        try:
            print(
                f"[DEBUG] Buscando informações de pagamento no Mercado Pago: {payment_id}")
            payment_info = self.mp_service.sdk.payment().get(payment_id)
            payment_data = payment_info.get("response", {})
            print(f"[DEBUG] Dados do pagamento recebidos: {payment_data}")

        except Exception as e:
            print(f"[DEBUG] ERRO ao buscar pagamento: {str(e)}")
            return JsonResponse({"error": f"failed to fetch payment: {str(e)}"}, status=500)

        if payment_data.get("status") != "approved":
            return JsonResponse({"status": "pending_or_failed"})

        status = payment_data.get("status")
        print(f"[DEBUG] Status do pagamento: {status}")

        if status != "approved":
            print("[DEBUG] Pagamento ainda não aprovado ou falhou")
            return JsonResponse({"status": "pending_or_failed"})

        metadata = payment_data.get("metadata", {})
        print(f"[DEBUG] Metadata extraída: {metadata}")

        payment_type = metadata.get("type")
        user_id = metadata.get("user_id")

        print(f"[DEBUG] Tipo de pagamento: {payment_type}, user_id: {user_id}")

        if payment_type == "credits":
            amount = metadata.get("amount")
            print(f"[DEBUG] Processando crédito de coins | amount={amount}")
            self._process_wallet_credit(
                user_id=user_id,
                amount=metadata.get("amount"),
                payment_id=payment_id
            )
            print("[DEBUG] Crédito de carteira concluído com sucesso")
            return JsonResponse({"status": "wallet_updated"})

        if payment_type == "plan":
            plan_id = metadata.get("plan_id")
            print(f"[DEBUG] Processando ativação de plano | plan_id={plan_id}")
            self._activate_subscription(
                user_id=user_id,
                plan_id=metadata.get("plan_id")
            )
            print("[DEBUG] Assinatura ativada com sucesso")
            return JsonResponse({"status": "subscription_activated"})

        print("[DEBUG] Nenhum tipo válido de pagamento encontrado na metadata")
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
