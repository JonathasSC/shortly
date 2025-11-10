from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings

from apps.notification.tasks import send_welcome_email_task

User = get_user_model()


@override_settings(CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPAGATES=True)
class SendWelcomeEmailTaskTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="jon",
            email="jon@example.com",
            password="123"
        )

    def test_send_welcome_email_sends_email(self):
        send_welcome_email_task.delay(self.user.id)

        self.assertEqual(len(mail.outbox), 1)

        email = mail.outbox[0]
        self.assertIn("Bem-vindo", email.subject)
        self.assertIn(self.user.username, email.body)
        self.assertIn(self.user.email, email.to)
        self.assertTrue(email.alternatives)
