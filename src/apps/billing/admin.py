from django.contrib import admin
from django.utils.html import format_html

from apps.billing.models import Plan, UserSubscription, UserWallet, WalletTransaction


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "monthly_credits",
        "price",
        "disable_interstitial_page",
        "advanced_stats",
        "longtime_expiration_date",
        "conditional_redirect",
        "priority_support"
    )
    search_fields = ("name",)
    list_filter = (
        "disable_interstitial_page",
        "advanced_stats",
        "longtime_expiration_date",
        "conditional_redirect",
        "priority_support"
    )


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "plan", "status",
                    "start_date", "end_date", "auto_renew")
    list_filter = ("status", "auto_renew")
    search_fields = ("user__username", "plan__name")


@admin.register(UserWallet)
class UserWalletAdmin(admin.ModelAdmin):
    list_display = ("user", "balance")
    readonly_fields = ("balance",)
    fields = ("user", "balance")


@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = ("wallet", "transaction_type", "amount", "created_at")
    list_filter = ("transaction_type", "created_at")
    search_fields = ("wallet__user__username", "external_reference")

    def safe_user(self, obj):
        if obj.wallet and obj.wallet.user:
            return obj.wallet.user
        return format_html("<i>Usuário removido</i>")

    safe_user.short_description = "Usuário"
