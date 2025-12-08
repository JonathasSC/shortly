import hashlib
import hmac
import json
import logging

import mercadopago
from axes.decorators import axes_dispatch
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
from apps.billing.tasks import process_payment_task

logger = logging.getLogger(__name__)


class BuyCoinsView(LoginRequiredMixin, View):
    prices = {
        10: 5.99,
        20: 10.99,
        50: 24.99,
        100: 39.99,
    }

    def get(self, request, credit_amount, *args, **kwargs):
        logger.info(f"[COMPRA INICIADA] User={request.user.id} Credits={credit_amount}")

        sdk = mercadopago.SDK(settings.MERCADO_PAGO_ACCESS_TOKEN)
        mp_service = MercadoPagoService(sdk)

        if credit_amount not in self.prices:
            logger.warning(
                f"[PACOTE INVÁLIDO] User={request.user.id} Tentou comprar: {credit_amount} créditos"
            )
            return redirect("payment_failure")

        price = self.prices[credit_amount]
        logger.debug(f"[VALIDAÇÃO OK] User={request.user.id} Package={credit_amount} Price={price}")

        success_url = request.build_absolute_uri(reverse("payment_success")).replace("http://", "https://")
        failure_url = request.build_absolute_uri(reverse("payment_failure")).replace("http://", "https://")

        logger.debug(f"[BACK_URLS] Success={success_url} - Failure={failure_url}")

        notification_url = request.build_absolute_uri(reverse("mp_webhook")).replace("http://", "https://")
        
        logger.info(notification_url)
        
        preference = mp_service.create_checkout_preference(
            title=f"{credit_amount} Créditos",
            price=self.prices[credit_amount],
            quantity=1,
            back_urls={
                "success": success_url,
                "failure": failure_url,
                "pending": failure_url,
            },
            auto_return="approved",
            metadata={
                "user_id": str(request.user.id),
                "type": "credits",
                "amount": credit_amount,
            },
            notification_url=notification_url
        )
        
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
    def get(self, request, plan_id, *args, **kwargs):
        try:
            sdk = mercadopago.SDK(settings.MERCADO_PAGO_ACCESS_TOKEN)
            mp_service = MercadoPagoService(sdk)
            plan = Plan.objects.get(id=plan_id)
            logger.info(f"Usuário {request.user.id} iniciou assinatura do plano {plan_id}")

        except Plan.DoesNotExist:
            logger.warning(f"Plano {plan_id} não encontrado para assinatura por {request.user.id}")
            return redirect("payment_failure")

        success_url = request.build_absolute_uri(reverse("payment_success"))
        failure_url = request.build_absolute_uri(reverse("payment_failure"))

        preference = mp_service.create_checkout_preference(
            title=f"Assinatura: {plan.name}",
            price=plan.price,
            quantity=1,
            back_url_success=success_url,
            back_url_failure=failure_url,
            metadata={"user_id": str(request.user.id), "type": "plan", "plan_id": plan.id},
        )

        logger.info(
            f"Preferência de pagamento criada para assinatura do plano {plan_id} pelo usuário {request.user.id}"
        )
        return redirect(preference["response"]["init_point"])

@method_decorator(csrf_exempt, name="dispatch")
@method_decorator(axes_dispatch(disable=True), name="dispatch")
class MercadoPagoWebhookView(View):
    sdk = mercadopago.SDK(settings.MERCADO_PAGO_ACCESS_TOKEN)
    mp_service = MercadoPagoService(sdk)

    def post(self, request, *args, **kwargs):
        logger.info("[WEBHOOK] POST recebido")
        return self.handle_webhook(request)

    def _process_wallet_credit(self, user_id, amount, payment_id):
        logger.info(f"[CREDITO] Iniciando crédito | user={user_id} amount={amount} payment={payment_id}")

        User = get_user_model()
        try:
            User.objects.get(pk=user_id)
        except User.DoesNotExist:
            logger.error(f"[CREDITO] Usuário não encontrado | user={user_id}")
            raise ValueError("user_not_found")

        try:
            amount = int(float(amount))
        except (TypeError, ValueError):
            logger.error(f"[CREDITO] Valor inválido | user={user_id} amount={amount}")
            return {"status": "invalid_amount"}

        if WalletTransaction.objects.filter(external_reference=payment_id).exists():
            logger.warning(f"[CREDITO] Já processado | payment={payment_id}")
            return {"status": "already_processed"}

        wallet, _ = UserWallet.objects.get_or_create(user_id=user_id)

        with transaction.atomic():
            wallet.credit(amount)
            WalletTransaction.objects.create(
                wallet=wallet,
                amount=amount,
                transaction_type=WalletTransaction.TransactionType.CREDIT,
                source=f"Crédito via Mercado Pago: {amount}",
                external_reference=str(payment_id),
            )

        logger.info(f"[CREDITO] Sucesso | user={user_id} amount={amount}")
        return {"status": "wallet_updated"}

    def _activate_subscription(self, user_id, plan_id):
        logger.info(f"[ASSINATURA] Ativando | user={user_id} plan={plan_id}")
        plan = Plan.objects.get(id=plan_id)
        UserSubscription.objects.update_or_create(
            user_id=user_id, defaults={"plan": plan, "is_active": True}
        )
        logger.info(f"[ASSINATURA] Ativada com sucesso | user={user_id} plan={plan_id}")

    def _verify_signature(self, request):
        try:
            x_signature = request.headers.get("x-signature")
            x_request_id = request.headers.get("x-request-id")
            url = request.build_absolute_uri()

            if not x_signature:
                print("[SIGNATURE] Ausente")
                return False

            print(f"[SIGNATURE] Recebida: {x_signature}")

            # Tenta extrair ID do evento dos query params (payments aprovados usam isto)
            data_id = request.GET.get("data.id")

            # Caso não exista, tenta extrair do corpo JSON
            if not data_id:
                try:
                    request.json if hasattr(request, "json") else request.body
                    body = request.data if hasattr(request, "data") else {}
                    data_id = body.get("data", {}).get("id")
                except Exception:
                    pass

            print(f"[WEBHOOK] DATA ID = {data_id}")

            # Extrai ts e v1 da assinatura
            parts = x_signature.split(",")
            ts = None
            hash_v1 = None

            for p in parts:
                key, value = p.split("=")
                if key == "ts":
                    ts = value
                elif key == "v1":
                    hash_v1 = value

            if not ts or not hash_v1:
                print("[SIGNATURE] ts ou v1 ausentes")
                return False

            secret = settings.MERCADO_PAGO_WEBHOOK_SECRET

            signed_parts = []

            if data_id:
                signed_parts.append(f"id:{data_id};")

            if x_request_id:
                signed_parts.append(f"request-id:{x_request_id};")

            if ts:
                signed_parts.append(f"ts:{ts};")

            if "url=" in x_signature.lower(): 
                signed_parts.append(f"url:{url}")

            signed_string = ''.join(signed_parts)
            print(f"[SIGNATURE] Manifest final: {signed_string}")
            
            hmac_result = hmac.new(
                key=secret.encode("utf-8"),
                msg=signed_string.encode("utf-8"),
                digestmod=hashlib.sha256
            ).hexdigest()

            print(f"[SIGNATURE] HMAC Calculado: {hmac_result}")

            if hmac.compare_digest(hmac_result, hash_v1):
                print("[SIGNATURE] ✔ Assinatura válida!")
                return True

            print("[SIGNATURE] ❌ Assinatura inválida!")
            return False

        except Exception as e:
            print(f"[ERROR] Verificando assinatura: {e}")
            return False


    def handle_webhook(self, request):
        logger.info("[WEBHOOK] Payload recebido")

        if not self._verify_signature(request):
            logger.error("[WEBHOOK] Assinatura negada")
            return JsonResponse({"error": "invalid_signature"}, status=403)

        try:
            data = json.loads(request.body.decode("utf-8"))
            logger.debug(f"[WEBHOOK] Body: {data}")
        except Exception as e:
            logger.error(f"[WEBHOOK] JSON inválido: {e}")
            data = {}

        topic = data.get("topic") or data.get("type")
        if topic not in ("payment", "approved", "payment.updated", "payment.created"):
            logger.info(f"[WEBHOOK] Evento ignorado | topic={topic}")
            return JsonResponse({"status": "ignored"})

        payment_id = (
            data.get("id") or data.get("data.id") or (data.get("data", {}) or {}).get("id")
        )

        if not payment_id:
            logger.error("[WEBHOOK] ID de pagamento não encontrado")
            return JsonResponse({"error": "id_missing"}, status=400)

        logger.info(f"[WEBHOOK] Buscando detalhes do pagamento | id={payment_id}")

        payment_info = self.mp_service.sdk.payment().get(payment_id)
        payment_data = payment_info.get("response", {})

        logger.debug(f"[WEBHOOK] PaymentData={payment_data}")

        status = payment_data.get("status")
        metadata = payment_data.get("metadata") or {}
        print('metadata: ', metadata)
        payment_type = metadata.get("type")
        user_id = metadata.get("user_id")

        logger.info(f"[WEBHOOK] Status={status} Tipo={payment_type} User={user_id}")

        if status != "approved":
            logger.info("[WEBHOOK] Pagamento pendente/negado. Aguardando atualização.")
            return JsonResponse({"status": "pending"})

        if WalletTransaction.objects.filter(external_reference=str(payment_id)).exists():
            logger.warning(f"[WEBHOOK] Já processado | payment={payment_id}")
            return JsonResponse({"status": "already_processed"}, status=200)

        if payment_type == "credits":
            logger.info(f"[WEBHOOK] Aprovado (créditos), enviando para fila | payment={payment_id}")
            process_payment_task.delay(
                user_id=user_id,
                payment_type=payment_type,
                amount=metadata.get("amount"),
                payment_id=payment_id
            )
            return JsonResponse({"status": "queued"}, status=202)

        if payment_type == "plan":
            plan_id = metadata.get("plan_id")
            logger.info(f"[WEBHOOK] Aprovado (plano) | payment={payment_id}")
            self._activate_subscription(user_id, plan_id)
            return JsonResponse({"status": "subscription_activated"})

        logger.info("[WEBHOOK] Tipo desconhecido. Ignorando.")
        return JsonResponse({"status": "ignored"})


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
        transactions = WalletTransaction.objects.filter(wallet=wallet).order_by("-created_at")

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

