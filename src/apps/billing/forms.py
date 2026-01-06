from django import forms

from apps.billing.models import WalletTransaction
from apps.billing.services.wallet_service import WalletService


class WalletAdjustmentForm(forms.Form):
    amount = forms.IntegerField()
    reason = forms.CharField()


class WalletTransactionAdminForm(forms.ModelForm):
    class Meta:
        model = WalletTransaction
        fields = ("wallet", "transaction_type", "amount",
                  "source", "external_reference")

    def save(self, commit=True):
        wallet = self.cleaned_data["wallet"]
        amount = self.cleaned_data["amount"]
        tx_type = self.cleaned_data["transaction_type"]
        source = self.cleaned_data["source"]
        ref = self.cleaned_data["external_reference"]

        if tx_type == WalletTransaction.TransactionType.CREDIT:
            return WalletService.credit(wallet, amount, source, ref)
        else:
            return WalletService.debit(wallet, amount, source, ref)
