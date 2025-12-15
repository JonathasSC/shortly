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

from apps.billing.models import Plan, UserSubscription, UserWallet, WalletTransaction
from apps.billing.services import MercadoPagoService

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class MercadoPagoWebhookView(View):
    sdk = mercadopago.SDK(settings.MERCADO_PAGO_ACCESS_TOKEN)
    mp_service = MercadoPagoService(sdk)

    def _process_wallet_credit(self, user_id, amount, payment_id):
        logger.info(
            f"Processando crédito na carteira: user={user_id}, amount={amount}, payment={payment_id}")
        try:
            User = get_user_model()
            User.objects.get(pk=user_id)
        except User.DoesNotExist:
            logger.error(
                f"Usuário {user_id} não encontrado para crédito de carteira.")
            raise ValueError("user_not_found")

        try:
            amount = int(float(amount))
        except (TypeError, ValueError):
            logger.error(f"Valor inválido para crédito de carteira: {amount}")
            return {"status": "invalid_amount"}

        if WalletTransaction.objects.filter(external_reference=payment_id).exists():
            logger.warning(f"Transação já processada: {payment_id}")
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

        logger.info(f"Crédito de {amount} coins aplicado ao usuário {user_id}")
        return {"status": "wallet_updated"}

    def _activate_subscription(self, user_id, plan_id):
        logger.info(f"Ativando assinatura: user={user_id}, plan={plan_id}")
        plan = Plan.objects.get(id=plan_id)
        UserSubscription.objects.update_or_create(
            user_id=user_id,
            defaults={"plan": plan, "is_active": True}
        )
        logger.info(
            f"Assinatura ativada com sucesso: user={user_id}, plan={plan_id}")

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
            logger.warning(
                "Assinatura ausente ou ID de pagamento não encontrado.")
            return False

        message = f"id:{payment_id};request-id:{x_request_id}".encode("utf-8")
        expected_hmac = hmac.new(
            secret.encode("utf-8"),
            message,
            hashlib.sha256
        ).hexdigest()

        valid = hmac.compare_digest(expected_hmac, x_signature)
        if not valid:
            logger.warning(f"Assinatura inválida para pagamento {payment_id}")
        return valid

    def handle_webhook(self, request):
        logger.info("Recebendo webhook do Mercado Pago.")

        if not self._verify_signature(request):
            logger.error("Assinatura HMAC inválida recebida.")
            return JsonResponse({"error": "invalid_signature"}, status=403)

        if request.content_type == "application/json":
            try:
                data = json.loads(request.body.decode("utf-8"))
            except Exception as e:
                logger.error(f"Erro ao decodificar corpo JSON: {str(e)}")
                data = {}
        else:
            data = request.GET or request.POST

        topic = data.get("topic") or data.get("type")
        if topic != "payment":
            logger.info("Webhook ignorado: tipo não é 'payment'.")
            return JsonResponse({"status": "ignored"})

        payment_id = (
            data.get("id")
            or data.get("data.id")
            or (data.get("data", {}) or {}).get("id")
        )

        if not payment_id:
            logger.error("Webhook recebido sem ID de pagamento.")
            return JsonResponse({"error": "id not found"}, status=400)

        try:
            payment_info = self.mp_service.sdk.payment().get(payment_id)
            payment_data = payment_info.get("response", {})
            logger.info(f"Pagamento {payment_id} recuperado do Mercado Pago.")
        except Exception as e:
            logger.exception(
                f"Falha ao obter pagamento {payment_id}: {str(e)}")
            return JsonResponse({"error": f"failed to fetch payment: {str(e)}"}, status=500)

        if payment_data.get("status") != "approved":
            logger.info(
                f"Pagamento {payment_id} não aprovado. Status: {payment_data.get('status')}")
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
                logger.info(f"Créditos processados com resultado: {result}")
                return JsonResponse(result)
            except ValueError as e:
                logger.error(f"Erro de valor ao processar créditos: {str(e)}")
                return JsonResponse({"error": str(e)}, status=400)
            except Exception as e:
                logger.exception(
                    f"Erro inesperado ao processar créditos: {str(e)}")
                return JsonResponse({"error": "internal_error"}, status=500)

        if payment_type == "plan":
            self._activate_subscription(
                user_id=user_id,
                plan_id=metadata.get("plan_id")
            )
            logger.info(f"Assinatura ativada via pagamento {payment_id}")
            return JsonResponse({"status": "subscription_activated"})

        logger.warning(
            f"Webhook ignorado: tipo de pagamento inválido ({payment_type})")
        return JsonResponse({"status": "ignored_no_valid_type"})
