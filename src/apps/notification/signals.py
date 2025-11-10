from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.account.models import User
from apps.notification.tasks import send_welcome_email_task


user: User = get_user_model()


@receiver(post_save, sender=User)
def send_welcome_on_signup(sender, instance, created, **kwargs):
    if created:
        transaction.on_commit(
            lambda: send_welcome_email_task.apply_async(
                args=[instance.id],
                countdown=30
            )
        )
