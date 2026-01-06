from django.db import transaction
from django.utils import timezone

from apps.billing.models import UserSubscription


class SubscriptionService:

    @staticmethod
    @transaction.atomic
    def activate_plan(user, plan, auto_renew=True, end_date=None):
        UserSubscription.objects.filter(
            user=user,
            status=UserSubscription.Status.ACTIVE
        ).update(status=UserSubscription.Status.INACTIVE)

        subscription, _ = UserSubscription.objects.update_or_create(
            user=user,
            plan=plan,
            defaults={
                "status": UserSubscription.Status.ACTIVE,
                "start_date": timezone.now(),
                "end_date": end_date,
                "auto_renew": auto_renew,
            }
        )

        return subscription

    @staticmethod
    @transaction.atomic
    def cancel(subscription: UserSubscription):
        subscription.status = UserSubscription.Status.CANCELED
        subscription.auto_renew = False
        subscription.save(update_fields=["status", "auto_renew"])
