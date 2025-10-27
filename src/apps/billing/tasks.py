from celery import shared_task
from django.utils import timezone

from apps.billing.models import UserSubscription


@shared_task(ignore_result=True)
def disable_user_subscription():
    now = timezone.now()

    expired_subs = UserSubscription.objects.filter(
        end_date__lt=now,
        status=UserSubscription.Status.ACTIVE,
        auto_renew=False
    )

    count = expired_subs.count()
    expired_subs.update(status=UserSubscription.Status.INACTIVE)

    return f"{count} assinatura(s) inativada(s) por expiração sem renovação."
