from django.http import JsonResponse

from apps.security.services import ExponentialBanService


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
