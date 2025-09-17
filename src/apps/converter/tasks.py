from .models import Url
from celery import shared_task
from django.utils import timezone


@shared_task(ignore_result=True)
def delete_expired_urls():
    deleted, _ = Url.objects.filter(expires_at__lt=timezone.now()).delete()
    return f"{deleted} URLs expiradas removidas"
