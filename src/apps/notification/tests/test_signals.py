from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

User = get_user_model()


class SendWelcomeOnSignupSignalTest(TestCase):

    @patch("apps.notification.signals.transaction.on_commit")
    @patch("apps.notification.signals.send_welcome_email_task.apply_async")
    def test_signal_calls_task_after_user_creation(self, mock_apply_async, mock_on_commit):
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpassword"
        )

        registered_callback = mock_on_commit.call_args[0][0]

        registered_callback()

        mock_apply_async.assert_called_once_with(
            args=[user.id],
            countdown=30
        )
