from django.urls import path

from apps.manager.consumers import LogsConsumer

websocket_urlpatterns = [
    path("ws/admin/system/logs/", LogsConsumer.as_asgi()),
]
