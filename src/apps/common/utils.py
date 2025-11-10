# apps/notification/tests/utils.py
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save

from apps.notification.signals import send_welcome_on_signup

User = get_user_model()


class CommonUtils:
    def __init__(self):
        pass

    def disable_welcome_signal(self):
        post_save.disconnect(send_welcome_on_signup, sender=User)
