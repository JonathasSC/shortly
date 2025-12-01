from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.test import TestCase, override_settings
from django.utils import timezone

from apps.billing.models import (
    Plan,
    UserSubscription,
    UserWallet,
    WalletTransaction,
)
from apps.billing.signals import add_new_user_coins
from apps.notification.signals import send_welcome_on_signup

User = get_user_model()


class TestModels(TestCase):
    @override_settings(DISABLE_SIGNALS=True)
    def setUp(self):
        post_save.disconnect(send_welcome_on_signup, sender=User)
        post_save.disconnect(add_new_user_coins, sender=User)

    def tearDown(self):
        post_save.connect(send_welcome_on_signup, sender=User)
        post_save.connect(add_new_user_coins, sender=User)

    def test_plan_creation(self):
        plan = Plan.objects.create(
            name="Premium",
            monthly_credits=100,
            price=29.90,
            advanced_stats=True,
        )

        self.assertIsNotNone(plan.id)
        self.assertEqual(plan.name, "Premium")
        self.assertEqual(plan.monthly_credits, 100)
        self.assertTrue(plan.advanced_stats)

    def test_user_subscription_creation(self):
        user = User.objects.create_user("john", "john@test.com", "123")
        plan = Plan.objects.create(name="Basic")

        subscription = UserSubscription.objects.create(user=user, plan=plan)

        self.assertEqual(subscription.user, user)
        self.assertEqual(subscription.plan, plan)
        self.assertEqual(subscription.status, UserSubscription.Status.ACTIVE)
        self.assertEqual(subscription.start_date.date(), timezone.now().date())

    def test_wallet_credit(self):
        user = User.objects.create_user("ana", "ana@test.com", "123")
        wallet = UserWallet.objects.create(user=user)

        wallet.credit(10)
        self.assertEqual(wallet.balance, 10)

        wallet.credit(5)
        self.assertEqual(wallet.balance, 15)

    def test_wallet_debit_success(self):
        user = User.objects.create_user("mark", "mark@test.com", "123")
        wallet = UserWallet.objects.create(user=user, balance=10)

        result = wallet.debit(4)

        self.assertTrue(result)
        self.assertEqual(wallet.balance, 6)

    def test_wallet_debit_fail(self):
        user = User.objects.create_user("maria", "maria@test.com", "123")
        wallet = UserWallet.objects.create(user=user, balance=2)

        result = wallet.debit(5)

        self.assertFalse(result)
        self.assertEqual(wallet.balance, 2)

    def test_wallet_transaction_creation(self):
        user = User.objects.create_user("bob", "bob@test.com", "123")
        wallet = UserWallet.objects.create(user=user)

        WalletTransaction.objects.create(
            wallet=wallet,
            amount=50,
            transaction_type=WalletTransaction.TransactionType.CREDIT,
            source="Teste",
        )

        self.assertEqual(wallet.transactions.count(), 1)

        transaction = wallet.transactions.first()
        self.assertEqual(transaction.amount, 50)
        self.assertEqual(transaction.source, "Teste")
        self.assertEqual(transaction.transaction_type, "credit")
