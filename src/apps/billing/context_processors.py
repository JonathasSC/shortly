from apps.billing.models import UserWallet


class BillingContextProcessor:
    @staticmethod
    def user_balance(request):
        if request.user.is_authenticated:
            try:
                wallet = UserWallet.objects.get(user=request.user)
                return {'user_balance': wallet.balance}
            except UserWallet.DoesNotExist:
                return {'user_balance': 0}
        return {'user_balance': 0}


processor = BillingContextProcessor()
user_balance = processor.user_balance
