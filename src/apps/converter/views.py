import json
import secrets

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import models
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as translate
from django.views import View

from apps.converter.enums import PricingRule
from apps.converter.forms import UrlForm
from apps.converter.models import AccessEvent, Url, UrlMetadata
from apps.converter.services.pricing_service import PricingService
from apps.converter.services.shortening_service import ShortenResult, UrlShorteningService
from apps.converter.utils import UserRequestUtil
from apps.notification.models import Announcement

user_request_util = UserRequestUtil()


class MiddleView(View):
    def get(self, request, short_code) -> HttpResponse:
        url = get_object_or_404(Url, short_code=short_code)
        metadata = get_object_or_404(UrlMetadata, url=url)
        
        ip_address = user_request_util.get_client_ip(request)

        AccessEvent.objects.create(url=url, ip_address=ip_address)

        if metadata.is_direct:
            return redirect(url.original_url)

        token = secrets.token_urlsafe(16)
        request.session[f"token_{token}"] = {
            "timestamp": timezone.now().timestamp(),
            "target_url": url.original_url,
        }

        return render(request, "converter/middle.html", {
            "redirect_url": reverse("converter:confirm-redirect") + f"?token={token}",
        })


class ConfirmRedirectView(View):
    def get(self, request):
        token = request.GET.get("token")
        data = request.session.get(f"token_{token}")

        if not data:
            return HttpResponseForbidden("Token inválido")

        now = timezone.now().timestamp()
        if now - data["timestamp"] < 5:
            return HttpResponseForbidden("Aguarde 5 segundos")

        del request.session[f"token_{token}"]
        return redirect(data["target_url"])


class HomeView(View):
    def get(self, request):
        form = UrlForm()
        announcements = []
        pricing = {
            "base": PricingService.RULE_COSTS[PricingRule.BASE],
            "direct": PricingService.RULE_COSTS[PricingRule.DIRECT],
            "permanent": PricingService.RULE_COSTS[PricingRule.PERMANENT],
        }
        
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
            {
                "form": form,
                "announcements": announcements,
                "pricing": json.dumps(pricing),
            },
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
                is_permanent=form.cleaned_data["is_permanent"],
                create_new=request.POST.get("create_new") == "true"
            )
        except ValidationError:
            messages.success(request, mark_safe(
                render_to_string(
                    "converter/includes/insufficient_balance.html")
            ))
            return redirect("converter:home")

        if result == ShortenResult.EXISTS:
            messages.info(
                request,
                mark_safe(
                    render_to_string(
                        "converter/includes/existing_url_trigger.html",
                        {
                            "original_url": url.original_url,
                            "is_direct": form.cleaned_data["is_direct"],
                            "is_permanent": form.cleaned_data["is_permanent"],
                        },
                    )
                ),
            )
            return redirect("converter:home")

        short_url = request.build_absolute_uri(
            f"/{url.short_code}/").replace("http", "https")
        
        metadata = UrlMetadata.objects.filter(url=url).first()

        messages.success(
            request,
            mark_safe(
                render_to_string(
                    "converter/includes/url_created.html",
                    {
                        "short_url": short_url,
                        "is_direct": metadata.is_direct,
                        "is_permanent": metadata.is_permanent,
                    },
                )
            ),
        )
        return redirect("converter:home")
