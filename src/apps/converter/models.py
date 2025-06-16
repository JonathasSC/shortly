from django.db import models
from .utils import ShortCodeGenerator
from django.core.validators import URLValidator


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

    def save(self, *args, **kwargs):
        if not self.short_code:
            self.short_code = short_code_generator.generate_unique(
                Url, 'short_code')
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.short_code} -> {self.original_url}"
