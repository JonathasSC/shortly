from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import AccessEvent, Url, UrlMetadata, UrlSequence


class UrlMetadataInline(admin.StackedInline):
    model = UrlMetadata
    can_delete = False
    verbose_name_plural = _("Configurações de Redirecionamento")
    fields = ("is_direct", "is_permanent")


@admin.register(Url)
class UrlAdmin(admin.ModelAdmin):
    inlines = [UrlMetadataInline]

    list_display = (
        "short_code",
        "get_short_link",
        "display_original_url",
        "get_is_direct",
        "get_access_count",
        "created_at",
    )

    list_filter = (
        "metadata__is_direct",
        "metadata__is_permanent",
        "created_at",
    )

    search_fields = (
        "short_code",
        "original_url",
        "created_by_ip",
    )

    ordering = ("-created_at",)

    readonly_fields = (
        "short_code",
        "created_at",
        "updated_at",
        "created_by_ip",
    )

    fieldsets = (
        (_("Informações Básicas"), {
            "fields": ("short_code", "original_url"),
        }),
        (_("Rastreamento"), {
            "fields": ("created_by_ip", "created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    @admin.display(description=_("Short Link"))
    def get_short_link(self, obj):
        url = f"/{obj.short_code}/"
        return format_html('<a href="{}" target="_blank">{}</a>', url, url)

    @admin.display(description=_("Original URL"))
    def display_original_url(self, obj):
        return (
            obj.original_url[:50] + "..."
            if len(obj.original_url) > 50
            else obj.original_url
        )

    @admin.display(description=_("Direct?"), boolean=True)
    def get_is_direct(self, obj):
        return obj.metadata.is_direct if hasattr(obj, "metadata") else False

    @admin.display(description=_("Acessos"))
    def get_access_count(self, obj):
        count = obj.accessevent_set.count()
        if count > 0:
            url = f"/admin/converter/accessevent/?url__id__exact={obj.id}"
            return format_html('<a href="{}">{} acessos</a>', url, count)
        return "0"


@admin.register(AccessEvent)
class AccessEventAdmin(admin.ModelAdmin):
    list_display = (
        "url",
        "ip_address",
        "country",
        "region",
        "city",
        "browser",
        "os",
        "device_type",
        "is_bot",
        "created_at",
    )

    list_filter = (
        "is_bot",
        "browser",
        "os",
        "device_type",
        "country",
        "created_at",
    )

    search_fields = (
        "url__short_code",
        "ip_address",
        "user_agent",
        "city",
        "country",
        "region",
    )

    ordering = ("-created_at",)

    readonly_fields = (
        "url",
        "ip_address",
        "user_agent",
        "referer",
        "browser",
        "browser_version",
        "os",
        "device_type",
        "country",
        "region",
        "city",
        "latitude",
        "longitude",
        "is_bot",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (_("Informações Principais"), {
            "fields": ("url", "ip_address", "is_bot"),
        }),
        (_("Navegador / Dispositivo"), {
            "fields": ("browser", "browser_version", "os", "device_type"),
            "classes": ("collapse",),
        }),
        (_("Localização"), {
            "fields": ("country", "region", "city", "latitude", "longitude"),
            "classes": ("collapse",),
        }),
        (_("Requisição"), {
            "fields": ("user_agent", "referer"),
            "classes": ("collapse",),
        }),
        (_("Controle"), {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )


@admin.register(UrlSequence)
class UrlSequenceAdmin(admin.ModelAdmin):
    list_display = ("id", "value")
    readonly_fields = ("value",)