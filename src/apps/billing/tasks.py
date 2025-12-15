import logging

from celery import shared_task
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from apps.billing.models import Plan, UserSubscription, UserWallet, WalletTransaction

logger = logging.getLogger(__name__)


@shared_task(ignore_result=True)
def disable_user_subscription():
    now = timezone.now()

    expired_subs = UserSubscription.objects.filter(
        end_date__lt=now,
        status=UserSubscription.Status.ACTIVE,
        auto_renew=False
    )

    count = expired_subs.count()
    expired_subs.update(status=UserSubscription.Status.INACTIVE)

    return f"{count} assinatura(s) inativada(s) por expiração sem renovação."


@shared_task(bind=True, max_retries=5)
def process_payment_task(self, user_id, payment_type, amount=None, plan_id=None, payment_id=None):
    logger.info(
        f"[TASK][START] Processando pagamento | payment={payment_id} user={user_id} tipo={payment_type}")

    User = get_user_model()

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        logger.error(f"[TASK] Usuário não encontrado | user={user_id}")
        return {"status": "user_not_found"}

    if WalletTransaction.objects.filter(external_reference=str(payment_id)).exists():
        logger.warning(
            f"[TASK][Idempotência] Já processado | payment={payment_id}")
        return {"status": "already_processed"}

    if payment_type == "credits":
        logger.debug(
            f"[TASK] Iniciando aplicação de créditos | valor={amount}")

        wallet, created = UserWallet.objects.get_or_create(user=user)

        if created:
            logger.info(
                f"[TASK] Carteira criada para o usuário | user={user_id}")

        try:
            with transaction.atomic():
                tx = WalletTransaction.objects.create(
                    wallet=wallet,
                    amount=int(amount),
                    transaction_type=WalletTransaction.TransactionType.CREDIT,
                    status=WalletTransaction.Status.PENDING,
                    source=f"CRED {amount} via Mercado Pago",
                    external_reference=str(payment_id),
                )
                logger.info(
                    f"[TASK] Transação criada | tx_id={tx.id} status=PENDING")

                tx.process_success()
                logger.info(
                    f"[TASK] Transação marcada como SUCCESS | tx_id={tx.id}")

        except Exception as e:
            logger.error(
                f"[TASK][ERRO] Falha ao processar créditos | payment={payment_id} error={str(e)}")
            self.retry(exc=e, countdown=10)

        logger.info(
            f"[TASK][DONE] Créditos aplicados com sucesso | user={user_id} new_balance={wallet.balance}")
        return {"status": "wallet_updated", "transaction_id": tx.id}

    elif payment_type == "plan":
        logger.debug(f"[TASK] Iniciando ativação de plano | plan_id={plan_id}")

        try:
            plan = Plan.objects.get(id=plan_id)
        except Plan.DoesNotExist:
            logger.error(f"[TASK] Plano inexistente | plan_id={plan_id}")
            return {"status": "plan_not_found"}

        _, created = UserSubscription.objects.update_or_create(
            user=user,
            defaults={"plan": plan, "status": UserSubscription.Status.ACTIVE},
        )

        logger.info(
            f"[TASK][DONE] Assinatura ativada | user={user_id} "
            f"plan={plan_id} nova={created}"
        )

        return {"status": "subscription_activated"}

    logger.warning(
        f"[TASK] Tipo de pagamento não reconhecido | tipo={payment_type}")
    return {"status": "invalid_type"}
