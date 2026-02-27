from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from .models import Url


@shared_task(ignore_result=True)
def delete_expired_urls():
    expiration_date = timezone.now() - timedelta(days=7)

    deleted, _ = Url.objects.filter(
        metadata__is_permanent=False,
        created_at__lt=expiration_date,
    ).delete()

    return f"{deleted} URLs expiradas removidas"