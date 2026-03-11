
import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
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
        return self.subscriptions.filter(
            status=UserSubscription.Status.ACTIVE,
            end_date__isnull=True
        ).select_related("plan").first()

    @property
    def has_active_subscription(self):
        return self.subscriptions.filter(
            status=UserSubscription.Status.ACTIVE,
            end_date__isnull=True
        ).exists()


class UserDeletionSchedule(BaseModelAbstract):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    requested_at = models.DateTimeField(auto_now_add=True)
    scheduled_for = models.DateTimeField()
    reason = models.CharField(max_length=255, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)


def user_avatar_upload_path(instance, filename):
    ext = filename.split(".")[-1].lower()
    return f"users/{instance.user.id}/avatar/{uuid.uuid4().hex}.{ext}"


class UserProfile(BaseModelAbstract):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile"
    )

    avatar = models.ImageField(
        upload_to=user_avatar_upload_path,
        null=True,
        blank=True
    )

    bio = models.TextField(
        max_length=500,
        blank=True
    )

    website = models.URLField(
        blank=True
    )

    location = models.CharField(
        max_length=255,
        blank=True
    )

    birth_date = models.DateField(
        null=True,
        blank=True
    )

    is_verified = models.BooleanField(
        default=False
    )

    def __str__(self):
        return f"{self.user.username} profile"
