from django.urls import re_path

from apps.manager.consumers import LogsConsumer

websocket_urlpatterns = [
    re_path(r"logs/", LogsConsumer.as_asgi()),
]
