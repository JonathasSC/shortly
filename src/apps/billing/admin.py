from django.contrib import admin

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
    search_fields = ("user__username",)


@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = ("wallet", "transaction_type",
                    "amount", "source", "created_at")
    list_filter = ("transaction_type", "created_at")
    search_fields = ("wallet__user__username", "source")
