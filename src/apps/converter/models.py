from datetime import timedelta

from django.core.validators import URLValidator
from django.db import models
from django.utils import timezone

from apps.common.models import BaseModelAbstract
from apps.converter.utils import ShortCodeGenerator

short_code_generator: ShortCodeGenerator = ShortCodeGenerator(length=8)


class UrlSequence(models.Model):
    value = models.BigIntegerField(default=0)

    class Meta:
        db_table = "url_sequence"

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

    created_by_ip = models.GenericIPAddressField(
        null=True,
        blank=True
    )

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        from apps.converter.services.shortening_service import ShortCodeService, UrlSequenceService

        if is_new and not self.short_code:
            sequence = UrlSequenceService.next()
            self.short_code = ShortCodeService.encode(sequence)

        super().save(*args, **kwargs)

    def is_expired(self) -> bool:
        return timezone.now() > self.created_at + timedelta(days=7)

    def __str__(self):
        return f"{self.short_code} -> {self.original_url}"


class AccessEvent(BaseModelAbstract):
    url = models.ForeignKey(Url, on_delete=models.CASCADE)
    ip_address = models.TextField(max_length=15)


class UrlMetadata(BaseModelAbstract):
    url = models.OneToOneField(
        Url,
        on_delete=models.CASCADE,
        related_name="metadata",
    )
    is_direct = models.BooleanField(default=False)
    is_permanent = models.BooleanField(default=False)
