
from django.db import IntegrityError, transaction
from django.db.models import F
from django.utils.translation import gettext_lazy as translate

from apps.account.dtos.create_user_dto import CreateUserDTO
from apps.account.models import User
from apps.billing.models import UserWallet, WalletTransaction


class CreateUserService:
    @staticmethod
    @transaction.atomic
    def execute(dto: CreateUserDTO) -> User:        
        try:
            user = User.objects.create_user(
                username=dto.username,
                email=dto.email,
                password=dto.password
            )
        except IntegrityError:
            return User.objects.get(username=dto.username)

        wallet, _ = UserWallet.objects.get_or_create(user=user)

        updated = UserWallet.objects.filter(
            pk=wallet.pk,
            balance=0
        ).update(balance=F("balance") + 5)

        if updated:
            WalletTransaction.objects.create(
                wallet=wallet,
                amount=5,
                transaction_type=WalletTransaction.TransactionType.CREDIT,
                source=translate("%(amount)s free coins for signing up") % {"amount": 5}
            )
    
        return user
