from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone

from apps.common.models import BaseModelAbstract


class Plan(BaseModelAbstract):
    name = models.CharField(max_length=50, unique=True)
    monthly_credits = models.PositiveIntegerField(default=0)
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    disable_interstitial_page = models.BooleanField(default=True)
    advanced_stats = models.BooleanField(default=False)
    longtime_expiration_date = models.BooleanField(default=False)
    conditional_redirect = models.BooleanField(default=False)
    priority_support = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} - R$ {self.price}"


class UserSubscription(BaseModelAbstract):
    def default_subscription_end():
        return timezone.now() + timedelta(days=30)

    class Status(models.TextChoices):
        ACTIVE = "active", "Ativa"
        INACTIVE = "inactive", "Inativa"
        CANCELED = "canceled", "Cancelada"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscriptions"
    )
    plan = models.ForeignKey(
        Plan,
        on_delete=models.SET_NULL,
        null=True
    )
    start_date = models.DateTimeField(
        default=timezone.now
    )
    end_date = models.DateTimeField(
        null=True,
        blank=True,
        default=default_subscription_end
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE
    )
    auto_renew = models.BooleanField(
        default=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "plan"],
                name="unique_user_plan_subscription"
            )
        ]

    def save(self, *args, **kwargs):
        if self.status == self.Status.ACTIVE:
            UserSubscription.objects.filter(
                user=self.user
            ).exclude(pk=self.pk).update(status=self.Status.INACTIVE)

        if not self.pk:
            existing = UserSubscription.objects.filter(
                user=self.user,
                plan=self.plan,
            ).first()

            if existing:
                existing.status = self.status
                existing.start_date = self.start_date
                existing.end_date = self.end_date
                existing.auto_renew = self.auto_renew
                existing.save()
                return

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user} - {self.plan} ({self.status})"


class UserWallet(BaseModelAbstract):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="wallet"
    )
    balance = models.PositiveIntegerField(
        default=0
    )

    def _credit(self, amount: int):
        if amount <= 0:
            raise ValidationError("Valor de crédito inválido.")
        self.balance += amount

    def _debit(self, amount: int):
        if amount <= 0:
            raise ValidationError("Valor de débito inválido.")
        if self.balance < amount:
            raise ValidationError("Saldo insuficiente.")
        self.balance -= amount

    def __str__(self):
        return f"{self.user} - {self.balance} coins"


class WalletTransaction(BaseModelAbstract):

    class TransactionType(models.TextChoices):
        CREDIT = "credit", "Crédito"
        DEBIT = "debit", "Débito"

    class Status(models.TextChoices):
        PENDING = "pending", "Pendente"
        SUCCESS = "success", "Concluída"
        FAILED = "failed", "Falhou"
        REFUNDED = "refunded", "Estornada"

    wallet = models.ForeignKey(
        UserWallet,
        on_delete=models.CASCADE,
        related_name="transactions"
    )
    transaction_type = models.CharField(
        max_length=10,
        choices=TransactionType.choices
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING
    )
    amount = models.PositiveIntegerField()
    processed_at = models.DateTimeField(
        null=True,
        blank=True
    )
    source = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )
    external_reference = models.CharField(
        max_length=128,
        blank=True,
        null=True,
        unique=True
    )

    # --------------------------------------

    def _apply(self, wallet):
        if self.transaction_type == self.TransactionType.CREDIT:
            wallet._credit(self.amount)
        else:
            wallet._debit(self.amount)

        wallet.save(update_fields=["balance"])
        self.processed_at = timezone.now()

    def save(self, *args, **kwargs):
        creating = self._state.adding

        with transaction.atomic():
            wallet = UserWallet.objects.select_for_update().get(pk=self.wallet.pk)

            if creating and self.status == self.Status.SUCCESS:
                self._apply(wallet)

            if not creating:
                old_status = type(self).objects.get(pk=self.pk).status
                if old_status != self.Status.SUCCESS and self.status == self.Status.SUCCESS:
                    self._apply(wallet)

            self.full_clean()
            super().save(*args, **kwargs)

    # --------------------------------------

    def process_success(self):
        if self.status != self.Status.PENDING:
            raise ValidationError(
                "Somente transações pendentes podem ser concluídas.")
        self.status = self.Status.SUCCESS
        self.save(update_fields=["status"])

    def process_failed(self):
        if self.status != self.Status.PENDING:
            raise ValidationError("Somente transações pendentes podem falhar.")
        self.status = self.Status.FAILED
        self.save(update_fields=["status"])

    # --------------------------------------

    def refund(self):
        if self.status != self.Status.SUCCESS:
            raise ValidationError(
                "Somente transações concluídas podem ser estornadas.")

        reverse_type = (
            self.TransactionType.DEBIT
            if self.transaction_type == self.TransactionType.CREDIT
            else self.TransactionType.CREDIT
        )

        WalletTransaction.objects.create(
            wallet=self.wallet,
            transaction_type=reverse_type,
            amount=self.amount,
            status=self.Status.SUCCESS,
            source=f"Refund of #{self.pk}",
        )

        self.status = self.Status.REFUNDED
        self.save(update_fields=["status"])

    def __str__(self):
        return f"{self.transaction_type} {self.amount} {self.status}"
