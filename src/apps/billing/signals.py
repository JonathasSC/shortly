from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.billing.models import UserWallet, WalletTransaction

User = get_user_model()


@receiver(post_save, sender=User)
def add_new_user_coins(sender, instance, created, **kwargs):
    if not created:
        return

    wallet, _ = UserWallet.objects.get_or_create(user=instance)
    amount = 5

    def schedule_email():
        with transaction.atomic():
            WalletTransaction.objects.create(
                wallet=wallet,
                amount=amount,
                transaction_type=WalletTransaction.TransactionType.CREDIT,
                source=f"{amount} moedas grátis ao se registrar",
            )

    transaction.on_commit(schedule_email)
