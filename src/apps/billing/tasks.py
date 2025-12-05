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
    logger.info(f"Task: processando pagamento {payment_id} para user {user_id}")

    User = get_user_model()
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        logger.error(f"Usuário {user_id} não encontrado.")
        return {"status": "user_not_found"}

    if WalletTransaction.objects.filter(external_reference=str(payment_id)).exists():
        logger.warning(f"[Idempotência] Pagamento {payment_id} já processado.")
        return {"status": "already_processed"}

    if payment_type == "credits":
        wallet, _ = UserWallet.objects.get_or_create(user=user)

        with transaction.atomic():
            tx = WalletTransaction.objects.create(
                wallet=wallet,
                amount=int(amount),
                transaction_type=WalletTransaction.TransactionType.CREDIT,
                status=WalletTransaction.Status.PENDING,
                source=f"CRED {amount} via Mercado Pago",
                external_reference=str(payment_id),
            )

            tx.process_success()

        logger.info(f"Crédito aplicado com sucesso! User={user_id}")
        return {"status": "wallet_updated", "transaction_id": tx.id}

    elif payment_type == "plan":
        plan = Plan.objects.get(id=plan_id)
        UserSubscription.objects.update_or_create(
            user=user,
            defaults={"plan": plan, "is_active": True},
        )
        logger.info(f"Assinatura ativada com sucesso! User={user_id}")
        return {"status": "subscription_activated"}

    return {"status": "invalid_type"}
