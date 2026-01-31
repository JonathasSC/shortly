
from django.http import JsonResponse

from apps.security.services import ExponentialBanService, WebSocketOriginService


class ExponentialBanMiddleware:
    LOGIN_URLS = ["/login/", "/api/login/"]

    def __init__(self, get_response=None):
        self.get_response = get_response

    def __call__(self, request):
        if request.path in self.LOGIN_URLS:
            username = request.POST.get("username")
            if username:
                remaining = ExponentialBanService.get_ban_remaining(username)
                if remaining > 0:
                    return JsonResponse(
                        {"detail": f"Usuário bloqueado por {remaining} segundos"},
                        status=429,
                    )

        return self.get_response(request)


class WsAllowedOriginValidator:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "websocket":
            return await self.app(scope, receive, send)

        headers = {
            key.decode().lower(): value.decode()
            for key, value in scope.get("headers", [])
        }

        origin = headers.get("origin")

        if not WebSocketOriginService.is_allowed(origin):
            await send({
                "type": "websocket.close",
                "code": 4003,
            })
            return

        return await self.app(scope, receive, send)
