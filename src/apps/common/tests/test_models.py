import time

from django.contrib.auth import get_user_model
from django.db import connection, models
from django.test import TransactionTestCase

from apps.common.models import BaseModelAbstract
from apps.common.utils import CommonUtils


class ExampleModel(BaseModelAbstract):
    name = models.CharField(max_length=100)

    class Meta:
        app_label = 'common'


class BaseModelAbstractTest(TransactionTestCase):
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

    def test_create_instance(self):
        instance = ExampleModel.objects.create(
            name="teste", created_by=self.user)
        self.assertIsNotNone(instance.id)
        self.assertEqual(instance.created_by, self.user)

    def test_created_by_and_updated_by_fields(self):
        instance = ExampleModel.objects.create(
            name="Exemplo", created_by=self.user)
        self.assertEqual(instance.created_by, self.user)
        self.assertIsNone(instance.updated_by)

        instance.updated_by = self.user
        instance.save()
        instance.refresh_from_db()
        self.assertEqual(instance.updated_by, self.user)

    def test_auto_now_and_auto_now_add_behavior(self):
        instance = ExampleModel.objects.create(
            name="Teste", created_by=self.user)
        old_updated_at = instance.updated_at

        instance.name = "Teste atualizado"
        time.sleep(1)
        instance.save()
        instance.refresh_from_db()

        self.assertGreater(instance.updated_at, old_updated_at)

    def test_fields_editable_false_behavior(self):
        field_names = [
            f.name for f in ExampleModel._meta.fields if not f.editable]
        self.assertIn("id", field_names)
        self.assertIn("created_at", field_names)
        self.assertIn("created_by", field_names)
        self.assertIn("updated_by", field_names)

    def test_string_representation(self):
        instance = ExampleModel.objects.create(
            name="Meu exemplo", created_by=self.user)
        self.assertEqual(str(instance), f"ExampleModel object ({instance.id})")
