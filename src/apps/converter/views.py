import io
import json
import secrets

import qrcode
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Count
from django.http import Http404, HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as translate
from django.views import View

from apps.converter.enums import PricingRule
from apps.converter.forms import UrlForm
from apps.converter.models import Url, UrlMetadata
from apps.converter.services.access_event_service import AccessEventService
from apps.converter.services.pricing_service import PricingService
from apps.converter.services.shortening_service import ShortenResult, UrlShorteningService
from apps.converter.utils import UserRequestUtil
from apps.notification.models import Announcement

user_request_util = UserRequestUtil()


class MiddleView(View):
    def get(self, request, short_code) -> HttpResponse:
        url = get_object_or_404(Url, short_code=short_code)
        metadata = get_object_or_404(UrlMetadata, url=url)
        AccessEventService.track(request, url)

        if metadata.is_direct:
            return redirect(url.original_url)

        token = secrets.token_urlsafe(16)
        request.session[f"token_{token}"] = {
            "timestamp": timezone.now().timestamp(),
            "target_url": url.original_url,
        }

        return render(
            request,
            "converter/middle.html",
            {
                "redirect_url": reverse("converter:confirm-redirect") + f"?token={token}",
            },
        )


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
            if announcement.show_only_once and str(announcement.id) in seen:
                continue

            announcements.append(announcement)

        if announcements:
            updated_seen = seen[:]

            for ann in announcements:
                ann_id_str = str(ann.id)
                if ann.show_only_once and ann_id_str not in updated_seen:
                    updated_seen.append(ann_id_str)

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
                url_object=form.save(commit=True),
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
            f"/{url.short_code}").replace("http", "https")

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


def _generate_qr_png(data: str) -> bytes:
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#18181b", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


class UrlDetailView(LoginRequiredMixin, View):
    login_url = "/account/login/"

    def get(self, request, short_code):
        url = get_object_or_404(Url, short_code=short_code)
        if url.created_by != request.user:
            raise Http404

        metadata = UrlMetadata.objects.filter(url=url).first()
        events = url.accessevent_set.all()

        total_clicks = events.count()
        unique_visitors = events.values("ip_address").distinct().count()

        top_countries = (
            events.exclude(country__isnull=True)
            .exclude(country="")
            .values("country")
            .annotate(total=Count("id"))
            .order_by("-total")[:5]
        )

        device_counts = (
            events.exclude(device_type__isnull=True)
            .values("device_type")
            .annotate(total=Count("id"))
            .order_by("-total")
        )

        short_url = request.build_absolute_uri(
            f"/{url.short_code}/").replace("http://", "https://")

        is_expired = url.is_expired()
        days_until_expiry = None
        if not is_expired and metadata and not metadata.is_permanent:
            delta = url.expires_at - timezone.now()
            days_until_expiry = max(0, delta.days)

        return render(request, "converter/url_detail.html", {
            "url": url,
            "metadata": metadata,
            "short_url": short_url,
            "total_clicks": total_clicks,
            "unique_visitors": unique_visitors,
            "top_countries": list(top_countries),
            "device_counts": list(device_counts),
            "is_expired": is_expired,
            "days_until_expiry": days_until_expiry,
        })


class QrCodeImageView(LoginRequiredMixin, View):
    login_url = "/account/login/"

    def get(self, request, short_code):
        url = get_object_or_404(Url, short_code=short_code)
        if url.created_by != request.user:
            raise Http404

        short_url = request.build_absolute_uri(
            f"/{url.short_code}/").replace("http://", "https://")
        png = _generate_qr_png(short_url)
        response = HttpResponse(png, content_type="image/png")
        response["Content-Disposition"] = f'inline; filename="qr-{short_code}.png"'
        response["Cache-Control"] = "private, max-age=3600"
        return response
