from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.billing.models import UserWallet, WalletTransaction


class WalletService:

    @staticmethod
    @transaction.atomic
    def credit(
        wallet: UserWallet,
        amount: int,
        source: str = None,
        external_reference: str = None
    ) -> WalletTransaction:
        if amount <= 0:
            raise ValidationError("O valor do crédito deve ser positivo.")

        transaction = WalletTransaction.objects.create(
            wallet=wallet,
            transaction_type=WalletTransaction.TransactionType.CREDIT,
            amount=amount,
            source=source,
            external_reference=external_reference,
        )

        wallet.balance += amount
        wallet.save(update_fields=["balance"])

        transaction.status = WalletTransaction.Status.SUCCESS
        transaction.processed_at = timezone.now()
        transaction.save(update_fields=["status", "processed_at"])

        return transaction

    @staticmethod
    @transaction.atomic
    def debit(wallet, amount, source=None, external_reference=None):
        if amount <= 0:
            raise ValidationError("O valor do débito deve ser positivo.")

        if wallet.balance < amount:
            raise ValidationError("Saldo insuficiente.")

        transaction = WalletTransaction.objects.create(
            wallet=wallet,
            transaction_type=WalletTransaction.TransactionType.DEBIT,
            amount=amount,
            source=source,
            external_reference=external_reference,
            status=WalletTransaction.Status.SUCCESS,
        )
        return transaction

    @staticmethod
    @transaction.atomic
    def refund(transaction: WalletTransaction) -> WalletTransaction:
        if transaction.status != WalletTransaction.Status.SUCCESS:
            raise ValidationError(
                "Apenas transações concluídas podem ser estornadas."
            )

        wallet = UserWallet.objects.select_for_update().get(
            pk=transaction.wallet.pk
        )

        reverse_type = (
            WalletTransaction.TransactionType.DEBIT
            if transaction.transaction_type == WalletTransaction.TransactionType.CREDIT
            else WalletTransaction.TransactionType.CREDIT
        )

        if reverse_type == WalletTransaction.TransactionType.DEBIT:
            if wallet.balance < transaction.amount:
                raise ValidationError("Saldo insuficiente para estorno.")
            wallet.balance -= transaction.amount
        else:
            wallet.balance += transaction.amount

        wallet.save(update_fields=["balance"])

        refund_transaction = WalletTransaction.objects.create(
            wallet=wallet,
            transaction_type=reverse_type,
            amount=transaction.amount,
            status=WalletTransaction.Status.SUCCESS,
            source=f"Refund: {transaction.id}",
            external_reference=transaction.external_reference,
            processed_at=timezone.now(),
        )

        transaction.status = WalletTransaction.Status.REFUNDED
        transaction.save(update_fields=["status"])

        return refund_transaction
