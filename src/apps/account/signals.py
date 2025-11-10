from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.notification.tasks import send_welcome_email_task

User = get_user_model()


@receiver(post_save, sender=User)
def send_welcome_on_signup(sender, instance, created, **kwargs):
    if not created:
        return

    def schedule_email():
        send_welcome_email_task.delay(instance.id)

    transaction.on_commit(schedule_email)
