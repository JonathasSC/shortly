from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.shortcuts import render
from django.views import View
from django.db.models import Count

from apps.converter.models import AccessEvent, Url


class DashboardHomeView(LoginRequiredMixin, View):
    login_url = '/account/login/'
    redirect_field_name = 'next'

    def get(self, request):
        user_links = Url.objects.filter(
            created_by=request.user).order_by('-created_at')

        total_links = user_links.count()

        total_accesses = AccessEvent.objects.filter(
            url__in=user_links).count()

        recent_links = user_links.annotate(
            clicks=Count('accessevent')
        ).order_by('-created_at')

        context = {
            "user_links": user_links,
            "total_links": total_links,
            "total_accesses": total_accesses,
            "recent_links": recent_links,
        }
        return render(request, 'dashboard/home.html', context)
