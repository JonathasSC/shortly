import time

from django.contrib.auth import get_user_model
from django.db import connection, models
from django.test import TransactionTestCase

from apps.billing.models import UserWallet, WalletTransaction
from apps.common.models import BaseModelAbstract
from apps.common.utils import CommonUtils
from django.db.models.signals import post_save
from apps.billing.signals import add_new_user_coins
from apps.notification.signals import send_welcome_on_signup


User = get_user_model()

class ExampleModel(BaseModelAbstract):
    name = models.CharField(max_length=100)

    class Meta:
        app_label = 'common'


class WalletTransactionTestCase(TransactionTestCase):
    reset_sequences = True

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        post_save.disconnect(add_new_user_coins, sender=User)
        post_save.disconnect(send_welcome_on_signup, sender=User)

    @classmethod
    def tearDownClass(cls):
        post_save.connect(add_new_user_coins, sender=User)
        post_save.connect(send_welcome_on_signup, sender=User)
        super().tearDownClass()
        

    def setUp(self):
        CommonUtils().disable_welcome_signal()
        self.user = get_user_model().objects.create_user(
            username="tester",
            email="tester@example.com",
            password="testpass123"
        )
        self.wallet = UserWallet.objects.create(user=self.user, balance=0)

    # ------------------------
    # WalletTransaction tests
    # ------------------------
    def test_create_pending_transaction(self):
        transaction = WalletTransaction.objects.create(
            wallet=self.wallet,
            amount=100,
            transaction_type=WalletTransaction.TransactionType.CREDIT,
            status=WalletTransaction.Status.PENDING,
            source="Test",
        )
        self.assertEqual(transaction.status, WalletTransaction.Status.PENDING)
        self.assertEqual(self.wallet.balance, 0)  # saldo não aplicado ainda

    def test_process_success_adds_balance(self):
        transaction = WalletTransaction.objects.create(
            wallet=self.wallet,
            amount=50,
            transaction_type=WalletTransaction.TransactionType.CREDIT,
            status=WalletTransaction.Status.PENDING,
            source="Test",
        )
        transaction.process_success()
        self.wallet.refresh_from_db()
        self.assertEqual(transaction.status, WalletTransaction.Status.SUCCESS)
        self.assertEqual(self.wallet.balance, 50)

    def test_process_failed_does_not_change_balance(self):
        transaction = WalletTransaction.objects.create(
            wallet=self.wallet,
            amount=50,
            transaction_type=WalletTransaction.TransactionType.CREDIT,
            status=WalletTransaction.Status.PENDING,
            source="Test",
        )
        transaction.process_failed()
        self.wallet.refresh_from_db()
        self.assertEqual(transaction.status, WalletTransaction.Status.FAILED)
        self.assertEqual(self.wallet.balance, 0)

    def test_refund_transaction(self):
        transaction = WalletTransaction.objects.create(
            wallet=self.wallet,
            amount=80,
            transaction_type=WalletTransaction.TransactionType.CREDIT,
            status=WalletTransaction.Status.PENDING,
            source="Test",
        )
        
        transaction.process_success()
        self.wallet.refresh_from_db()
        transaction.refund()
        
        self.wallet.refresh_from_db()
        self.assertEqual(transaction.status, WalletTransaction.Status.REFUNDED)
        self.assertEqual(self.wallet.balance, 0)

    def test_debit_transaction(self):
        # Adiciona saldo
        self.wallet.balance = 100
        self.wallet.save()

        transaction = WalletTransaction.objects.create(
            wallet=self.wallet,
            amount=40,
            transaction_type=WalletTransaction.TransactionType.DEBIT,
            status=WalletTransaction.Status.PENDING,
            source="Test",
        )
        transaction.process_success()
        self.wallet.refresh_from_db()
        self.assertEqual(transaction.status, WalletTransaction.Status.SUCCESS)
        self.assertEqual(self.wallet.balance, 60)

    def test_debit_transaction_insufficient_balance_raises(self):
        with self.assertRaises(ValueError):
            WalletTransaction.objects.create(
                wallet=self.wallet,
                amount=10,
                transaction_type=WalletTransaction.TransactionType.DEBIT,
                status=WalletTransaction.Status.PENDING,
                source="Test",
            ).process_success()
