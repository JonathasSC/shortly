import os
import django

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

from django.core.asgi import get_asgi_application
from apps.manager.ws_urls import websocket_urlpatterns
from apps.security.middleware import WsAllowedOriginValidator

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()


django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": WsAllowedOriginValidator(
        AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        ),
    )
})
