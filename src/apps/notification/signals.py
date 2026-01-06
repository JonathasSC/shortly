from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.account.models import User
from apps.notification.models import EmailOutbox


@receiver(post_save, sender=User)
def enqueue_welcome_email(sender, instance, created, **kwargs):
    if created:
        EmailOutbox.objects.create(user=instance, template="welcome")
