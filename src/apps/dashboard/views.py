from datetime import timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import OuterRef, Subquery, Count
from django.db.models.functions import TruncMonth
from django.shortcuts import render
from django.utils import timezone
from django.views import View

from apps.converter.models import AccessEvent, Url

from datetime import timedelta
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, OuterRef, Subquery
from django.db.models.functions import TruncMonth
from django.shortcuts import render
from django.utils import timezone
from django.views import View

from apps.converter.models import AccessEvent, Url


class DashboardHomeView(LoginRequiredMixin, View):
    login_url = '/account/login/'
    redirect_field_name = 'next'

    def get(self, request):
        clicks_subquery = (
            AccessEvent.objects.filter(url=OuterRef("pk"))
            .values("url")
            .annotate(clicks_count=Count("uuid"))
            .values("clicks_count")[:1]
        )

        user_urls = (
            Url.objects.filter(created_by=request.user)
            .annotate(clicks=Subquery(clicks_subquery))
            .prefetch_related("accessevent_set")
            .order_by("-created_at")
        )

        access_events = AccessEvent.objects.filter(url__created_by=request.user)

        total_urls = user_urls.count()
        total_access_events = access_events.count()

        now = timezone.now()
        seven_days_ago = now - timedelta(days=7)
        six_months_ago = now - timedelta(days=180)

        recent_urls_last_7_days = user_urls.filter(created_at__gte=seven_days_ago)
        total_accesses_last_6_months = access_events.filter(created_at__gte=six_months_ago).count()

        monthly_accesses = (
            access_events.filter(created_at__gte=six_months_ago)
            .annotate(month=TruncMonth("created_at"))
            .values("month")
            .annotate(total_clicks=Count("uuid"))
            .order_by("month")
        )
        monthly_labels = [entry["month"].strftime("%b/%Y") for entry in monthly_accesses]
        monthly_data = [entry["total_clicks"] for entry in monthly_accesses]

        top_clicked_urls = user_urls.filter(clicks__gt=0).order_by("-clicks")[:10]
        top_urls_labels = [url.short_code for url in top_clicked_urls]
        top_urls_clicks = [url.clicks or 0 for url in top_clicked_urls]

        context = {
            "user_links": user_urls,
            "total_links": total_urls,
            "total_accesses": total_access_events,
            "recent_links": user_urls,
            "seven_days_ago_links": recent_urls_last_7_days,
            "six_months_accesses": total_accesses_last_6_months,
            "line_labels": monthly_labels,
            "line_data": monthly_data,
            "pie_labels": top_urls_labels,
            "pie_data": top_urls_clicks,
        }

        return render(request, "dashboard/home.html", context)
