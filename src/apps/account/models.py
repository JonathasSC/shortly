from django.db import models
from django.contrib.auth.models import AbstractUser
from apps.common.models import BaseModelAbstract
from django.utils.translation import gettext_lazy as _


class User(BaseModelAbstract, AbstractUser):
    email = models.EmailField(_("email address"), blank=True)
    
    class Meta:
        verbose_name = "Usuário customizado"
        verbose_name_plural = "Usuários customizados"