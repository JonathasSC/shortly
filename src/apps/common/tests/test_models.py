import time
from django.contrib.auth import get_user_model
from django.db import connection, models, transaction
from django.test import TransactionTestCase

from apps.common.models import BaseModelAbstract
from apps.common.utils import CommonUtils
from apps.billing.models import UserWallet, WalletTransaction


class ExampleModel(BaseModelAbstract):
    name = models.CharField(max_length=100)

    class Meta:
        app_label = 'common'


class WalletTransactionTestCase(TransactionTestCase):
    reset_sequences = True

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with connection.cursor() as cursor:
            tables = connection.introspection.table_names(cursor)

        if ExampleModel._meta.db_table not in tables:
            with connection.schema_editor() as schema_editor:
                schema_editor.create_model(ExampleModel)

    @classmethod
    def tearDownClass(cls):
        with connection.schema_editor() as schema_editor:
            schema_editor.delete_model(ExampleModel)
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
    # BaseModelAbstract tests
    # ------------------------
    def test_create_example_instance(self):
        instance = ExampleModel.objects.create(
            name="teste", created_by=self.user)
        self.assertIsNotNone(instance.id)
        self.assertEqual(instance.created_by, self.user)

    def test_auto_now_and_auto_now_add(self):
        instance = ExampleModel.objects.create(
            name="Teste", created_by=self.user)
        old_updated_at = instance.updated_at

        instance.name = "Atualizado"
        time.sleep(1)
        instance.save()
        instance.refresh_from_db()
        self.assertGreater(instance.updated_at, old_updated_at)

    # ------------------------
    # WalletTransaction tests
    # ------------------------
    def test_create_pending_transaction(self):
        tx = WalletTransaction.objects.create(
            wallet=self.wallet,
            amount=100,
            transaction_type=WalletTransaction.TransactionType.CREDIT,
            status=WalletTransaction.Status.PENDING,
            source="Test",
        )
        self.assertEqual(tx.status, WalletTransaction.Status.PENDING)
        self.assertEqual(self.wallet.balance, 0)  # saldo não aplicado ainda

    def test_process_success_adds_balance(self):
        tx = WalletTransaction.objects.create(
            wallet=self.wallet,
            amount=50,
            transaction_type=WalletTransaction.TransactionType.CREDIT,
            status=WalletTransaction.Status.PENDING,
            source="Test",
        )
        tx.process_success()
        self.wallet.refresh_from_db()
        self.assertEqual(tx.status, WalletTransaction.Status.SUCCESS)
        self.assertEqual(self.wallet.balance, 50)

    def test_process_failed_does_not_change_balance(self):
        tx = WalletTransaction.objects.create(
            wallet=self.wallet,
            amount=50,
            transaction_type=WalletTransaction.TransactionType.CREDIT,
            status=WalletTransaction.Status.PENDING,
            source="Test",
        )
        tx.process_failed()
        self.wallet.refresh_from_db()
        self.assertEqual(tx.status, WalletTransaction.Status.FAILED)
        self.assertEqual(self.wallet.balance, 0)

    def test_refund_transaction(self):
        tx = WalletTransaction.objects.create(
            wallet=self.wallet,
            amount=80,
            transaction_type=WalletTransaction.TransactionType.CREDIT,
            status=WalletTransaction.Status.PENDING,
            source="Test",
        )
        tx.process_success()
        tx.refund()
        self.wallet.refresh_from_db()
        self.assertEqual(tx.status, WalletTransaction.Status.REFUNDED)
        self.assertEqual(self.wallet.balance, 0)

    def test_debit_transaction(self):
        # Adiciona saldo
        self.wallet.balance = 100
        self.wallet.save()

        tx = WalletTransaction.objects.create(
            wallet=self.wallet,
            amount=40,
            transaction_type=WalletTransaction.TransactionType.DEBIT,
            status=WalletTransaction.Status.PENDING,
            source="Test",
        )
        tx.process_success()
        self.wallet.refresh_from_db()
        self.assertEqual(tx.status, WalletTransaction.Status.SUCCESS)
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
