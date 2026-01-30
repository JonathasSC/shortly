from datetime import timedelta

from django.contrib.auth import get_user_model
from django.shortcuts import render
from django.utils import timezone
from django.views import View

from apps.converter.models import AccessEvent, Url

from .services.health.system_service import SystemStatusService

User = get_user_model()


class DashboardView(View):

    def _get_dates(self):
        today = timezone.localdate()
        yesterday = today - timedelta(days=1)
        return today, yesterday

    def _get_users_data(self, today, yesterday):
        return {
            "count_all_users": User.objects.count(),
            "count_users_today": User.objects.filter(date_joined__date=today).count(),
            "count_users_yesterday": User.objects.filter(date_joined__date=yesterday).count(),
            "count_active_users": User.objects.filter(is_active=True).count(),
        }

    def _get_urls_data(self, today):
        return {
            "count_created_urls_today": Url.objects.filter(created_at__date=today).count(),
            "count_clicks_today": AccessEvent.objects.filter(created_at__date=today).count(),
        }

    @staticmethod
    def percent_change(today, yesterday):
        if yesterday == 0:
            return 100 if today > 0 else 0
        return round(((today - yesterday) / yesterday) * 100, 1)

    def get(self, request):
        today, yesterday = self._get_dates()

        users_data = self._get_users_data(today, yesterday)
        urls_data = self._get_urls_data(today)

        context = {
            "users": users_data,
            "urls": urls_data,
            "users_growth": self.percent_change(
                users_data["count_users_today"],
                users_data["count_users_yesterday"]
            ),
        }
        context["system"] = SystemStatusService.get_status()

        return render(request, 'manager/dashboard.html', context)
