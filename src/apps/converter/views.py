import secrets

from django.contrib import messages
from django.db import models
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as translate
from django.views import View

from apps.converter.forms import UrlForm
from apps.converter.models import AccessEvent, Url
from apps.converter.services.url_shortening_service import UrlShorteningService, ShortenResult
from apps.converter.utils import UserRequestUtil
from apps.notification.models import Announcement
from django.core.exceptions import ValidationError

user_request_util = UserRequestUtil()


class MiddleView(View):
    def get(self, request, short_code) -> HttpResponse:
        url = get_object_or_404(Url, short_code=short_code)
        token = secrets.token_urlsafe(16)
        timestamp = timezone.now().timestamp()
        ip_address = user_request_util.get_client_ip(request)

        AccessEvent.objects.create(url=url, ip_address=ip_address)

        if url.is_direct:
            return redirect(url.original_url)

        request.session[f"token_{token}"] = {
            "timestamp": timestamp,
            "target_url": url.original_url,
        }

        return render(
            request,
            "converter/middle.html",
            {
                "redirect_url": reverse("confirm_redirect") + f"?token={token}",
            },
        )


class ConfirmRedirectView(View):
    def get(self, request):
        token = request.GET.get("token")
        if not token:
            return HttpResponseForbidden("Token inválido")

        data = request.session.get(f"token_{token}")
        if not data:
            return HttpResponseForbidden("Token não encontrado")

        timestamp = data.get("timestamp")
        target_url = data.get("target_url")

        if not target_url or timestamp is None:
            return HttpResponseForbidden("Dados incompletos")

        now = timezone.now().timestamp()
        if now - timestamp < 5:
            remaining = int(5 - (now - timestamp))
            return render(
                request,
                "converter/middle.html",
                {
                    "redirect_url": reverse("confirm_redirect") + f"?token={token}",
                    "remaining": remaining,
                },
            )

        del request.session[f"token_{token}"]
        return redirect(target_url)


class HomeView(View):
    def __get_existing_url(self, url_object, user, client_ip):
        if user.is_authenticated:
            return Url.objects.filter(
                original_url=url_object.original_url, created_by=user
            ).first()
        else:
            return Url.objects.filter(
                original_url=url_object.original_url, created_by=None, created_by_ip=client_ip
            ).first()

    def get(self, request):
        form = UrlForm()
        announcements = []

        now = timezone.now()

        queryset = Announcement.objects.filter(is_active=True, start_at__lte=now).filter(
            models.Q(end_at__isnull=True) | models.Q(end_at__gte=now)
        )

        seen = request.session.get("announcement_seen", [])

        for announcement in queryset:
            if announcement.show_only_once and announcement.id in seen:
                continue

            announcements.append(announcement)

        if announcements:
            updated_seen = seen[:]

            for ann in announcements:
                if ann.show_only_once and ann.id not in updated_seen:
                    updated_seen.append(ann.id)

            request.session["announcement_seen"] = updated_seen

        return render(
            request,
            "converter/home.html",
            {"form": form, "announcements": announcements},
        )

    def post(self, request):
        form = UrlForm(request.POST)
        client_ip = user_request_util.get_client_ip(request)

        if not form.is_valid():
            messages.error(request, translate("Invalid form"))
            return redirect("converter:home")

        try:
            url, result = UrlShorteningService.shorten(
                user=request.user,
                client_ip=client_ip,
                url_object=form.save(commit=False),
                is_direct=form.cleaned_data["is_direct"],
                create_new=request.POST.get("create_new") == "true"
            )
        except ValidationError:
            messages.success(request, mark_safe(
                render_to_string(
                    "converter/messages/insufficient_balance.html")
            ))
            return redirect("converter:home")

        if result == ShortenResult.EXISTS:
            messages.info(request, mark_safe(
                f'<span class="existing-url-trigger" data-original-url="{url.original_url}"></span>'
            ))
            return redirect("converter:home")

        short_url = request.build_absolute_uri(f"/{url.short_code}/")

        messages.success(request, mark_safe(
            render_to_string(
                "converter/success_message.html", {"short_url": short_url})
        ))
        return redirect("converter:home")
