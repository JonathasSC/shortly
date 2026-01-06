from django.db import models
from django.utils import timezone

from apps.common.models import BaseModelAbstract
from django.conf import settings


class Announcement(BaseModelAbstract):
    title = models.CharField(max_length=150, verbose_name="Título")

    message = models.TextField(verbose_name="Mensagem")

    is_active = models.BooleanField(default=True, verbose_name="Ativo")

    show_only_once = models.BooleanField(
        default=False, verbose_name="Exibir apenas uma vez por usuário"
    )

    start_at = models.DateTimeField(
        default=timezone.now, verbose_name="Início da exibição")
    end_at = models.DateTimeField(
        null=True, blank=True, verbose_name="Fim da exibição (opcional)")

    display_order = models.PositiveIntegerField(
        default=0, unique=True, verbose_name="Ordem de exibição")

    class Meta:
        ordering = ["display_order", "-start_at"]
        verbose_name = "Novidade"
        verbose_name_plural = "Novidades"

    def __str__(self):
        return self.title

    def is_available(self):
        now = timezone.now()
        if not self.is_active:
            return False
        if self.start_at and now < self.start_at:
            return False
        if self.end_at and now > self.end_at:
            return False
        return True


class EmailOutbox(BaseModelAbstract):
    class Status(models.TextChoices):
        PENDING = "pending"
        SENT = "sent"
        FAILED = "failed"

    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    template = models.CharField(max_length=50)
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.PENDING)
    attempts = models.PositiveSmallIntegerField(default=0)
    last_error = models.TextField(blank=True, null=True)

