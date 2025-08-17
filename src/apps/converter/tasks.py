from converter.models import Url
from celery import shared_task
from django.utils import timezone


@shared_task
def delete_expired_urls():
    deleted, _ = Url.objects.filter(expires_at__lt=timezone.now()).delete()
