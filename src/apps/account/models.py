
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.billing.models import UserSubscription
from apps.common.models import BaseModelAbstract


class User(BaseModelAbstract, AbstractUser):
    email = models.EmailField(_("email address"), unique=True)

    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"

    @property
    def active_subscription(self):
        now = timezone.now()
        return self.subscriptions.filter(
            status=UserSubscription.Status.ACTIVE,
            current_period_end__gte=now
        ).select_related("plan").order_by("-current_period_end").first()

    @property
    def has_active_subscription(self):
        now = timezone.now()
        return self.subscriptions.filter(
            status=UserSubscription.Status.ACTIVE,
            current_period_end__gte=now
        ).exists()


class UserDeletionSchedule(BaseModelAbstract):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    requested_at = models.DateTimeField(auto_now_add=True)
    scheduled_for = models.DateTimeField()
    reason = models.CharField(max_length=255, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
