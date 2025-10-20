from django.urls import path

from apps.dashboard.views import DashboardHomeView

urlpatterns = [
    path('', DashboardHomeView.as_view(), name='dashboard-home'),
]
