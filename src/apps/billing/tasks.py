import logging

from celery import shared_task
from django.contrib.auth import get_user_model
from django.db import transaction

from apps.billing.dto import PaymentDataDTO
from apps.billing.models import UserWallet, WalletTransaction
from apps.billing.services.wallet_service import WalletService

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=5)
def process_payment_task(self, data: PaymentDataDTO):
    logger.info(
        f"[TASK][START] Processando pagamento | payment={data.data.payment_id} user={data.user_id} tipo={data.payment_type}")

    User = get_user_model()

    try:
        user = User.objects.get(id=data.user_id)
    except User.DoesNotExist:
        logger.error(f"[TASK] Usuário não encontrado | user={data.user_id}")
        return {"status": "user_not_found"}

    if WalletTransaction.objects.filter(external_reference=str(data.payment_id)).exists():
        logger.warning(
            f"[TASK][Idempotência] Já processado | payment={data.payment_id}")
        return {"status": "already_processed"}

    if data.payment_type == "credits":
        logger.debug(
            f"[TASK] Iniciando aplicação de créditos | valor={data.amount}")

        wallet, created = UserWallet.objects.get_or_create(user=user)

        if created:
            logger.info(
                f"[TASK] Carteira criada para o usuário | user={data.user_id}")

        try:
            with transaction.atomic():
                wallet_transaction = WalletService.credit(
                    wallet=wallet,
                    amount=data.amount,
                    source=f"CRED {data.amount} via Mercado Pago",
                    external_reference=str(data.payment_id),
                )
                logger.info(
                    f"[TASK] Transação marcada como SUCCESS | wallet_transaction_id={wallet_transaction.id}")

        except Exception as e:
            logger.error(
                f"[TASK][ERRO] Falha ao processar créditos | payment={data.payment_id} error={str(e)}")
            self.retry(exc=e, countdown=10)

        logger.info(
            f"[TASK][DONE] Créditos aplicados com sucesso | user={data.user_id} new_balance={wallet.balance}")
        return {"status": "wallet_updated", "wallet_transaction_id": wallet_transaction.id}

    logger.warning(
        f"[TASK] Tipo de pagamento não reconhecido | tipo={data.payment_type}")
    return {"status": "invalid_type"}
