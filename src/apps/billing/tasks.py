import logging

from celery import shared_task
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from apps.billing.dto import PaymentDataDTO
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
                wallet_transaction = WalletTransaction.objects.create(
                    wallet=wallet,
                    amount=data.amount,
                    transaction_type=WalletTransaction.TransactionType.CREDIT,
                    status=WalletTransaction.Status.PENDING,
                    source=f"CRED {data.amount} via Mercado Pago",
                    external_reference=str(data.payment_id),
                )
                logger.info(
                    f"[TASK] Transação criada | wallet_transaction_id={wallet_transaction.id} status=PENDING")

                wallet_transaction.process_success()
                logger.info(
                    f"[TASK] Transação marcada como SUCCESS | wallet_transaction_id={wallet_transaction.id}")

        except Exception as e:
            logger.error(
                f"[TASK][ERRO] Falha ao processar créditos | payment={data.payment_id} error={str(e)}")
            self.retry(exc=e, countdown=10)

        logger.info(
            f"[TASK][DONE] Créditos aplicados com sucesso | user={data.user_id} new_balance={wallet.balance}")
        return {"status": "wallet_updated", "wallet_transaction_id": wallet_transaction.id}

    elif data.payment_type == "plan":
        logger.debug(
            f"[TASK] Iniciando ativação de plano | plan_id={data.plan_id}")

        try:
            plan = Plan.objects.get(id=data.plan_id)
        except Plan.DoesNotExist:
            logger.error(
                f"[TASK] Plano inexistente | plan_id={data.plan_id}")
            return {"status": "plan_not_found"}

        _, created = UserSubscription.objects.update_or_create(
            user=user,
            defaults={"plan": plan, "status": UserSubscription.Status.ACTIVE},
        )

        logger.info(
            f"[TASK][DONE] Assinatura ativada | user={data.user_id} "
            f"plan={data.plan_id} nova={created}"
        )

        return {"status": "subscription_activated"}

    logger.warning(
        f"[TASK] Tipo de pagamento não reconhecido | tipo={data.payment_type}")
    return {"status": "invalid_type"}


@shared_task(ignore_result=True)
def deposit_monthly_credits():
    now = timezone.now()
    subscriptions = UserSubscription.objects.filter(
        status=UserSubscription.Status.ACTIVE,
        start_date__lte=now,
        end_date__gte=now
    )

    total_transactions = 0

    for sub in subscriptions:
        user = sub.user
        plan = sub.plan

        if not plan.monthly_credits or plan.monthly_credits <= 0:
            logger.info(
                f"[TASK] Plano sem créditos mensais | user={user.id} plan={plan.id}")
            continue

        wallet, created = UserWallet.objects.get_or_create(user=user)

        if created:
            logger.info(
                f"[TASK] Carteira criada para o usuário | user={user.id}")

        try:
            with transaction.atomic():
                wallet_transaction = WalletTransaction.objects.create(
                    wallet=wallet,
                    amount=plan.monthly_credits,
                    transaction_type=WalletTransaction.TransactionType.CREDIT,
                    status=WalletTransaction.Status.PENDING,
                    source=f"Depósito mensal do plano {plan.name}",
                    external_reference=f"monthly_deposit_{now.strftime('%Y%m%d')}_{user.id}"
                )
                wallet_transaction.process_success()
                total_transactions += 1
                logger.info(
                    f"[TASK] Créditos depositados | user={user.id} amount={plan.monthly_credits}"
                )

        except Exception as e:
            logger.error(
                f"[TASK][ERRO] Falha ao depositar créditos | user={user.id} error={str(e)}"
            )

    logger.info(
        f"[TASK][DONE] Depósito mensal finalizado | total_transactions={total_transactions}")
    return {"status": "completed", "total_transactions": total_transactions}
