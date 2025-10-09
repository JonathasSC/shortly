from datetime import timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.shortcuts import render
from django.utils import timezone
from django.views import View

from apps.converter.models import AccessEvent, Url


class DashboardHomeView(LoginRequiredMixin, View):
    login_url = '/account/login/'
    redirect_field_name = 'next'

    def get(self, request):
        user_urls = Url.objects.filter(created_by=request.user).order_by('-created_at')

        total_urls = user_urls.count()
        total_access_events = AccessEvent.objects.filter(url__in=user_urls).count()

        seven_days_ago = timezone.now() - timedelta(days=7)
        recent_urls_last_7_days = user_urls.filter(created_at__gte=seven_days_ago)

        six_months_ago = timezone.now() - timedelta(days=180)
        total_accesses_last_6_months = AccessEvent.objects.filter(
            url__in=user_urls, created_at__gte=six_months_ago
        ).count()

        monthly_accesses_queryset = (
            AccessEvent.objects.filter(url__in=user_urls, created_at__gte=six_months_ago)
            .annotate(month=TruncMonth("created_at"))
            .values("month")
            .annotate(total_clicks=Count("uuid"))
            .order_by("month")
        )
        monthly_labels = [entry["month"].strftime("%b/%Y") for entry in monthly_accesses_queryset]
        monthly_clicks_data = [entry["total_clicks"] for entry in monthly_accesses_queryset]

        top_clicked_urls = (
            user_urls.annotate(clicks=Count("accessevent"))
            .filter(clicks__gt=0)
            .order_by('-clicks')[:10]
        )
        top_urls_labels = [url.short_code for url in top_clicked_urls]
        top_urls_clicks = [url.clicks for url in top_clicked_urls]

        recent_urls = user_urls.annotate(clicks=Count("accessevent")).order_by("-created_at")

        context = {
            "user_links": user_urls,
            "total_links": total_urls,
            "total_accesses": total_access_events,
            "recent_links": recent_urls,
            "seven_days_ago_links": recent_urls_last_7_days,
            "six_months_accesses": total_accesses_last_6_months,
            "line_labels": monthly_labels,
            "line_data": monthly_clicks_data,
            "pie_labels": top_urls_labels,
            "pie_data": top_urls_clicks,
        }

        return render(request, 'dashboard/home.html', context)
