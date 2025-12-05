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

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="subscriptions")
    plan = models.ForeignKey(Plan, on_delete=models.SET_NULL, null=True)
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    auto_renew = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user} - {self.plan} ({self.status})"


class UserWallet(models.Model):
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

    wallet = models.ForeignKey(UserWallet, on_delete=models.CASCADE, related_name="transactions")
    transaction_type = models.CharField(max_length=10, choices=TransactionType.choices)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    amount = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    source = models.CharField(max_length=50, blank=True, null=True)
    external_reference = models.CharField(max_length=128, blank=True, null=True)

    def process_success(self):
        if self.status != self.Status.PENDING:
            return

        with transaction.atomic():
            if self.transaction_type == self.TransactionType.CREDIT:
                self.wallet.balance += self.amount
            else:
                if self.wallet.balance < self.amount:
                    raise ValueError("Saldo insuficiente para débito.")
                self.wallet.balance -= self.amount

            self.wallet.save()

            self.status = self.Status.SUCCESS
            self.processed_at = timezone.now()
            self.save(update_fields=["status", "processed_at"])

    def process_failed(self):
        if self.status == self.Status.PENDING:
            self.status = self.Status.FAILED
            self.save(update_fields=["status"])

    def refund(self):
        if self.status != self.Status.SUCCESS:
            raise ValueError("Apenas transações concluídas podem ser estornadas.")

        with transaction.atomic():
            if self.transaction_type == self.TransactionType.CREDIT:
                self.wallet.balance -= self.amount
            else:
                self.wallet.balance += self.amount
            self.wallet.save()

            self.status = self.Status.REFUNDED
            self.processed_at = timezone.now()
            self.save(update_fields=["status", "processed_at"])

    def save(self, *args, **kwargs):
        if not self.pk and self.amount <= 0:
            raise ValueError("Valor precisa ser maior que zero.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError("Transações não podem ser apagadas por auditoria.")

    def __str__(self):
        return f"{self.transaction_type} {self.amount} {self.status} ({self.wallet.user})"