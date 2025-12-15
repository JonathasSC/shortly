from django.contrib import admin

from apps.toggler.models import FeatureFlag


@admin.register(FeatureFlag)
class FeatureFlagAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "enabled",
        "superuser_only",
        "rollout_percentage",
        "category",
        "updated_at",
    )
    list_filter = (
        "enabled",
        "superuser_only",
        "category",
    )
    search_fields = (
        "name",
        "description",
    )
    filter_horizontal = (
        "allowed_users",
        "allowed_groups",
    )

    fieldsets = (
        (None, {
            "fields": (
                "name",
                "description",
                "category",
                "enabled",
                "superuser_only",
            )
        }),
        ("Rollout Control", {
            "classes": ("collapse",),
            "fields": (
                "rollout_percentage",
                "allowed_users",
                "allowed_groups",
            )
        }),
        ("Metadata", {
            "classes": ("collapse",),
            "fields": (
                "created_at",
                "updated_at",
            )
        }),
    )

    readonly_fields = ("created_at", "updated_at")
