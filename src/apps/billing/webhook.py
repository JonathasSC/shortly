import hashlib
import hmac
import json
import logging

import mercadopago
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from apps.billing.dto import PaymentDataDTO
from apps.billing.models import UserWallet, WalletTransaction
from apps.billing.services.mp_service import MercadoPagoService
from apps.billing.services.wallet_service import WalletService
from apps.billing.tasks import process_payment_task

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name="dispatch")
class MercadoPagoWebhookView(View):
    sdk = mercadopago.SDK(settings.MERCADO_PAGO_ACCESS_TOKEN)
    mp_service = MercadoPagoService(sdk)

    def post(self, request, *args, **kwargs):
        logger.info("[WEBHOOK] POST recebido")
        return self.handle_webhook(request)

    def _process_wallet_credit(self, user_id, amount, payment_id):
        logger.info(
            f"[CREDITO] Iniciando crédito | user={user_id} amount={amount} payment={payment_id}")

        User = get_user_model()
        try:
            User.objects.get(pk=user_id)
        except User.DoesNotExist:
            logger.error(f"[CREDITO] Usuário não encontrado | user={user_id}")
            raise ValueError("user_not_found")

        try:
            amount = int(float(amount))
        except (TypeError, ValueError):
            logger.error(
                f"[CREDITO] Valor inválido | user={user_id} amount={amount}")
            return {"status": "invalid_amount"}

        if WalletTransaction.objects.filter(external_reference=payment_id).exists():
            logger.warning(f"[CREDITO] Já processado | payment={payment_id}")
            return {"status": "already_processed"}

        wallet, _ = UserWallet.objects.get_or_create(user_id=user_id)

        with transaction.atomic():
            WalletService.credit(
                wallet=wallet,
                amount=amount,
                source=f"Crédito via Mercado Pago: {amount}",
                external_reference=str(payment_id),
            )

        logger.info(f"[CREDITO] Sucesso | user={user_id} amount={amount}")
        return {"status": "wallet_updated"}

    def _verify_signature(self, request):
        try:
            x_signature = request.headers.get("x-signature")
            x_request_id = request.headers.get("x-request-id")
            url = request.build_absolute_uri()

            if not x_signature:
                return False

            data_id = request.GET.get("data.id")

            if not data_id:
                try:
                    request.json if hasattr(request, "json") else request.body
                    body = request.data if hasattr(request, "data") else {}
                    data_id = body.get("data", {}).get("id")
                except Exception:
                    pass

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

            hmac_result = hmac.new(
                key=secret.encode("utf-8"),
                msg=signed_string.encode("utf-8"),
                digestmod=hashlib.sha256
            ).hexdigest()

            if hmac.compare_digest(hmac_result, hash_v1):
                return True

            return False

        except Exception:
            return False

    def handle_webhook(self, request):
        logger.info("[WEBHOOK] Payload recebido")

        if not self._verify_signature(request):
            logger.warning("[WEBHOOK] Assinatura inválida — ignorada")
            return JsonResponse({"status": "ignored"}, status=200)

        try:
            data = json.loads(request.body.decode("utf-8"))
            logger.debug(f"[WEBHOOK] Body: {data}")
        except Exception as e:
            logger.error(f"[WEBHOOK] JSON inválido: {e}")
            data = {}

        topic = data.get("topic") or data.get("type")

        if topic in ("merchant_order", "topic_merchant_order_wh"):
            logger.info("[WEBHOOK] merchant_order recebido, buscando dados...")

            merchant_order_id = (
                data.get("id")
                or data.get("data.id")
                or (data.get("data", {}) or {}).get("id")
            )

            if not merchant_order_id:
                return JsonResponse({"error": "merchant_order_id_missing"}, status=400)

            merchant_order = self.mp_service.sdk.merchant_order().get(merchant_order_id)
            payments = merchant_order.get("response", {}).get("payments", [])

            if not payments:
                logger.info("[WEBHOOK] Sem pagamentos vinculados ainda")
                return JsonResponse({"status": "waiting_payment"})

            payment_id = payments[0].get("id")
            logger.info(
                f"[WEBHOOK] merchant_order encontrou pagamento | id={payment_id}")

            data["id"] = payment_id
            topic = "payment"

        if topic not in ("payment", "approved", "payment.updated", "payment.created"):
            logger.info(f"[WEBHOOK] Evento ignorado | topic={topic}")
            return JsonResponse({"status": "ignored"})

        payment_id = (
            data.get("id") or data.get("data.id") or (
                data.get("data", {}) or {}).get("id")
        )

        if not payment_id:
            logger.error("[WEBHOOK] ID de pagamento não encontrado")
            return JsonResponse({"error": "id_missing"}, status=400)

        logger.info(
            f"[WEBHOOK] Buscando detalhes do pagamento | id={payment_id}")

        payment_info = self.mp_service.sdk.payment().get(payment_id)
        payment_data = payment_info.get("response", {})

        logger.debug(f"[WEBHOOK] PaymentData={payment_data}")

        status = payment_data.get("status")
        metadata = payment_data.get("metadata") or {}

        payment_type = metadata.get("type")
        user_id = metadata.get("user_id")

        logger.info(
            f"[WEBHOOK] Status={status} Tipo={payment_type} User={user_id}")

        if status != "approved":
            logger.info(
                "[WEBHOOK] Pagamento pendente/negado. Aguardando atualização.")
            return JsonResponse({"status": "pending"})

        if WalletTransaction.objects.filter(external_reference=str(payment_id)).exists():
            logger.warning(f"[WEBHOOK] Já processado | payment={payment_id}")
            return JsonResponse({"status": "already_processed"}, status=200)

        if payment_type == "credits":
            logger.info(
                f"[WEBHOOK] Aprovado (créditos), enviando para fila | payment={payment_id}")

            payment_data = PaymentDataDTO(
                payment_id=payment_id,
                user_id=user_id,
                payment_type=payment_type,
                amount=metadata.get("amount"),
            )

            process_payment_task.delay(payment_data)
            return JsonResponse({"status": "queued"}, status=202)

        if payment_type == "plan":
            plan_id = metadata.get("plan_id")
            logger.info(f"[WEBHOOK] Aprovado (plano) | payment={payment_id}")
            self._activate_subscription(user_id, plan_id)
            return JsonResponse({"status": "subscription_activated"})

        logger.info("[WEBHOOK] Tipo desconhecido. Ignorando.")
        return JsonResponse({"status": "ignored"})
