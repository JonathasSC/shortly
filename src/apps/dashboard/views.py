from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View


class DashboardHomeView(LoginRequiredMixin, View):
    login_url = '/account/login/'
    redirect_field_name = 'next'

    def get(self, request):
        return render(request, 'dashboard/home.html')
