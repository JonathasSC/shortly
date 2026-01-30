from django.urls import path, re_path

from apps.manager.consumers import LogsConsumer
from .views import DashboardView

urlpatterns = [
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
]

websocket_urlpatterns = [
    re_path(r"ws/logs/$", LogsConsumer.as_asgi()),
]
