from django.contrib.auth import get_user_model
from django.db import models, transaction
from django.utils import timezone

User = get_user_model()


class Plan(models.Model):
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


class UserSubscription(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Ativa"
        INACTIVE = "inactive", "Inativa"
        CANCELED = "canceled", "Cancelada"

    user = models.ForeignKey(
        User,
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
        blank=True
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE
    )
    auto_renew = models.BooleanField(
        default=True
    )

    def __str__(self):
        return f"{self.user} - {self.plan} ({self.status})"


class UserWallet(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="wallet"
    )
    balance = models.PositiveIntegerField(
        default=0
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="wallet")
    balance = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.user} - {self.balance} coins"
    

class WalletTransaction(models.Model):
    class TransactionType(models.TextChoices):
        CREDIT = "credit", "Crédito"
        DEBIT = "debit", "Débito"

    class Status(models.TextChoices):
        PENDING = "pending", "Pendente"
        SUCCESS = "success", "Concluída"
        FAILED = "failed", "Falhou"
        REFUNDED = "refunded", "Estornada"

    wallet = models.ForeignKey(
        UserWallet, on_delete=models.CASCADE, related_name="transactions")
    transaction_type = models.CharField(
        max_length=10, choices=TransactionType.choices)
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.PENDING)
    class Status(models.TextChoices):
        PENDING = "pending", "Pendente"
        SUCCESS = "success", "Concluída"
        FAILED = "failed", "Falhou"
        REFUNDED = "refunded", "Estornada"

    wallet = models.ForeignKey(UserWallet, on_delete=models.CASCADE, related_name="transactions")
    transaction_type = models.CharField(max_length=10, choices=TransactionType.choices)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    amount = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    processed_at = models.DateTimeField(null=True, blank=True)
    
    source = models.CharField(max_length=50, blank=True, null=True)
    external_reference = models.CharField(max_length=128, blank=True, null=True)

    def _ensure_pending(self):
        if self.status != self.Status.PENDING:
            raise ValueError("Transação já foi processada e não pode ser alterada.")

    @transaction.atomic
    def process_success(self):
        self._ensure_pending()
        wallet = UserWallet.objects.select_for_update().get(pk=self.wallet.pk)

        if self.transaction_type == self.TransactionType.CREDIT:
            wallet.balance += self.amount
        elif self.transaction_type == self.TransactionType.DEBIT:
            if wallet.balance < self.amount:
                raise ValueError("Saldo insuficiente para débito.")
            wallet.balance -= self.amount

        wallet.save()
        self.status = self.Status.SUCCESS
        self.processed_at = timezone.now()
        self.save(update_fields=["status", "processed_at"])


    def process_failed(self):
        if self.status == self.Status.PENDING:
            self.status = self.Status.FAILED
            self.save(update_fields=["status"])


    @transaction.atomic
    def refund(self):
        if self.status != self.Status.SUCCESS:
            raise ValueError("Apenas transações concluídas podem ser estornadas.")

        reverse_type = (
            self.TransactionType.DEBIT
            if self.transaction_type == self.TransactionType.CREDIT
            else self.TransactionType.CREDIT
        )

        if reverse_type == self.TransactionType.DEBIT:
            if self.wallet.balance < self.amount:
                raise ValueError("Saldo insuficiente para estorno.")
            self.wallet.balance -= self.amount
        else:
            self.wallet.balance += self.amount

        self.wallet.save(update_fields=["balance"])

        WalletTransaction.objects.create(
            wallet=self.wallet,
            amount=self.amount,
            transaction_type=reverse_type,
            status=self.Status.SUCCESS,
            source=f"Refund: {self.id}",
            external_reference=self.external_reference,
        )

        self.status = self.Status.REFUNDED
        super(WalletTransaction, self).save(update_fields=["status"])


    def save(self, *args, **kwargs):
        if self.pk:  
            original = WalletTransaction.objects.get(pk=self.pk)
            if original.status == self.Status.SUCCESS:
                raise ValueError("Transações concluídas não podem ser alteradas.")

        if not self.pk and self.amount <= 0:
            raise ValueError("Valor precisa ser maior que zero.")
        
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError("Transações não podem ser apagadas por auditoria.")

    def __str__(self):
        return f"{self.transaction_type} {self.amount} {self.status} ({self.wallet.user})"