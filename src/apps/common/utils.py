# apps/notification/tests/utils.py
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save

from apps.notification.signals import enqueue_welcome_email

User = get_user_model()


class CommonUtils:
    def __init__(self):
        pass

    def disable_welcome_signal(self):
        post_save.disconnect(enqueue_welcome_email, sender=User)
