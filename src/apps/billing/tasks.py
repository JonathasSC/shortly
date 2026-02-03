import logging

from celery import shared_task
from django.contrib.auth import get_user_model
from django.db import transaction

from apps.billing.dto import PaymentDataDTO
from apps.billing.models import UserWallet, WalletTransaction
from apps.billing.services.wallet_service import WalletService

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=5)
def process_payment_task(self, data: dict):
    payment = PaymentDataDTO(**data)

    logger.info(
        f"[TASK][START] Processando pagamento | "
        f"payment={payment.payment_id} user={payment.user_id} tipo={payment.payment_type}"
    )

    User = get_user_model()

    try:
        user = User.objects.get(id=payment.user_id)
    except User.DoesNotExist:
        logger.error(f"[TASK] Usuário não encontrado | user={payment.user_id}")
        return {"status": "user_not_found"}

    if WalletTransaction.objects.filter(
        external_reference=str(payment.payment_id)
    ).exists():
        logger.warning(
            f"[TASK][Idempotência] Já processado | payment={payment.payment_id}"
        )
        return {"status": "already_processed"}

    if payment.payment_type == "credits":
        logger.debug(
            f"[TASK] Iniciando aplicação de créditos | valor={payment.amount}")

        wallet, created = UserWallet.objects.get_or_create(user=user)

        if created:
            logger.info(f"[TASK] Carteira criada | user={payment.user_id}")

        try:
            with transaction.atomic():
                wallet_transaction = WalletService.credit(
                    wallet=wallet,
                    amount=payment.amount,
                    source=f"CRED {payment.amount} via Mercado Pago",
                    external_reference=str(payment.payment_id),
                )

        except Exception as e:
            logger.error(
                f"[TASK][ERRO] Falha ao processar | payment={payment.payment_id} error={str(e)}"
            )
            raise self.retry(exc=e, countdown=10)

        wallet.refresh_from_db()

        logger.info(
            f"[TASK][DONE] Créditos aplicados | user={payment.user_id} balance={wallet.balance}"
        )
        return {"status": "wallet_updated", "wallet_transaction_id": wallet_transaction.id}

    logger.warning(f"[TASK] Tipo inválido | tipo={payment.payment_type}")
    return {"status": "invalid_type"}
