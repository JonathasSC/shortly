from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.test import TestCase

User = get_user_model()


class SendWelcomeOnSignupSignalTest(TestCase):
    @patch("apps.notification.signals.send_welcome_email_task.apply_async")
    @patch("apps.notification.signals.transaction.on_commit")
    def test_signal_calls_task_after_user_creation(self, mock_on_commit, mock_apply_async):
        def fake_on_commit(func, *args, **kwargs):
            func()

        mock_on_commit.side_effect = fake_on_commit

        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpassword",
        )

        mock_apply_async.assert_called_once_with(
            args=[user.id],
            countdown=30
        )
