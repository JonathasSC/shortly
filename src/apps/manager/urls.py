from django.urls import path, re_path

from .views import DashboardView

urlpatterns = [
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
]


def get_websocket_urlpatterns():
    from apps.manager.consumers import LogsConsumer
    return [
        re_path("ws/logs/", LogsConsumer.as_asgi()),
    ]
