from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.billing.models import UserWallet, WalletTransaction
from django.utils.translation import gettext_lazy as translate

from apps.billing.services.wallet_service import WalletService


User = get_user_model()


@receiver(post_save, sender=User)
def bootstrap_user_wallet(sender, instance, created, **kwargs):
    if not created:
        return

    wallet, _ = UserWallet.objects.get_or_create(user=instance)

    amount = 5

    def credit():
        WalletService.credit(
            wallet=wallet,
            amount=amount,
            source=translate("%(amount)s free coins for signing up") % {
                "amount": amount}
        )

    transaction.on_commit(credit)
