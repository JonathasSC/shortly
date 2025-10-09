from datetime import timedelta

from django.core.validators import URLValidator
from django.db import models
from django.utils import timezone

from apps.common.models import BaseModelAbstract
from apps.converter.utils import ShortCodeGenerator

short_code_generator: ShortCodeGenerator = ShortCodeGenerator(length=8)

class Url(BaseModelAbstract):
    original_url = models.URLField(
        max_length=4096,
        validators=[URLValidator()]
    )

    short_code = models.CharField(
        max_length=8,
        unique=True,
        editable=False
    )

    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Data/hora em que o link expira"
    )

    created_by_ip = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP do usuário anônimo que criou a URL"
    )

    def save(self, *args, **kwargs):
        if not self.short_code:
            self.short_code = short_code_generator.generate_unique(
                Url, 'short_code')
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=7)
        super().save(*args, **kwargs)

    def is_expired(self) -> bool:
        return self.expires_at and timezone.now() > self.expires_at

    def __str__(self):
        return f"{self.short_code} -> {self.original_url}"


class AccessEvent(BaseModelAbstract):
    url = models.ForeignKey(Url, on_delete=models.CASCADE)
    ip_address = models.TextField(max_length=15)
    created_at = models.DateTimeField(auto_now_add=True)
