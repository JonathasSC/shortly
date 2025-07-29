from django.db import models
from .utils import ShortCodeGenerator
from django.core.validators import URLValidator
from django.contrib.auth import get_user_model

short_code_generator: ShortCodeGenerator = ShortCodeGenerator(length=8)


class Url(models.Model):
    original_url = models.URLField(
        max_length=500,
        validators=[URLValidator()]
    )

    short_code = models.CharField(
        max_length=8,
        unique=True,
        editable=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    created_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        null=True,
        blank=True
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
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.short_code} -> {self.original_url}"


class AccessEvent(models.Model):
    url = models.ForeignKey(Url, on_delete=models.CASCADE)
    ip_address = models.TextField(max_length=15)
    created_at = models.DateTimeField(auto_now_add=True)
    counter = models.PositiveBigIntegerField()
