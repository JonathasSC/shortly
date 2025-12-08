from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _

from apps.account.models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Permissões"), {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        (_("Datas Importantes"), {"fields": ("last_login", "date_joined")}),
        (_("Informações Pessoais"), {"fields": ("first_name", "last_name")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "password1", "password2"),
        }),
    )

    readonly_fields = ("last_login", "date_joined")

    list_display = ("email", "is_staff", "is_active", "is_superuser")
    search_fields = ("email",)
    ordering = ("email",)

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def delete_model(self, request, obj):
        if not request.user.is_superuser:
            raise PermissionDenied("Você não tem permissão para excluir usuários")
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        if not request.user.is_superuser:
            raise PermissionDenied("Você não tem permissão para excluir usuários")
        super().delete_queryset(request, queryset)
