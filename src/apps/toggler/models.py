import hashlib
from typing import Optional

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser
from django.core.cache import cache
from django.db import models

from apps.common.models import BaseModelAbstract

User = get_user_model()

class FeatureFlag(BaseModelAbstract):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=50, blank=True, null=True)
    enabled = models.BooleanField(default=False)
    rollout_percentage = models.PositiveIntegerField(default=100)

    superuser_only = models.BooleanField(default=False)

    allowed_users = models.ManyToManyField(User, blank=True, related_name="feature_flags")
    allowed_groups = models.ManyToManyField("auth.Group", blank=True, related_name="feature_flags")

    CACHE_TIMEOUT = 60

    def __str__(self):
        return f"{self.name} - {'ON' if self.enabled else 'OFF'}"

    def is_active_for(self, user: Optional[AbstractBaseUser]) -> bool:

        cache_key = f"feature_flag:{self.pk}:{user.pk if user else 'anon'}"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        if not self.enabled:
            return False

        if self.superuser_only:
            allowed = bool(user and user.is_authenticated and user.is_superuser)
            cache.set(cache_key, allowed, self.CACHE_TIMEOUT)
            return allowed

        if user and user.is_authenticated:
            if self.allowed_users.filter(pk=user.pk).exists():
                cache.set(cache_key, True, self.CACHE_TIMEOUT)
                return True

            if self.allowed_groups.filter(pk__in=user.groups.all()).exists():
                cache.set(cache_key, True, self.CACHE_TIMEOUT)
                return True

        if user and user.is_authenticated:
            user_hash = int(hashlib.md5(str(user.pk).encode()).hexdigest(), 16)
            rollout_bucket = user_hash % 100
            if rollout_bucket < self.rollout_percentage:
                cache.set(cache_key, True, self.CACHE_TIMEOUT)
                return True

        cache.set(cache_key, False, self.CACHE_TIMEOUT)
        return False
