import json
from datetime import timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, OuterRef, Q, Subquery
from django.db.models.functions import TruncMonth
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views import View
from django.views.generic import ListView

from apps.converter.models import AccessEvent, Url


class DashboardHomeView(LoginRequiredMixin, View):
    login_url = "/account/login/"
    redirect_field_name = "next"

    def get(self, request):
        now = timezone.now()
        six_months_ago = now - timedelta(days=180)
        thirty_days_ago = now - timedelta(days=30)
        sixty_days_ago = now - timedelta(days=60)

        clicks_subquery = (
            AccessEvent.objects.filter(url=OuterRef("pk"))
            .values("url")
            .annotate(clicks_count=Count("id"))
            .values("clicks_count")[:1]
        )

        user_urls = (
            Url.objects.filter(created_by=request.user)
            .select_related("metadata")
            .annotate(clicks=Subquery(clicks_subquery))
            .order_by("-created_at")
        )

        access_events = AccessEvent.objects.filter(
            url__created_by=request.user
        )

        total_urls = user_urls.count()
        total_access_events = access_events.count()
        total_accesses_last_6_months = access_events.filter(
            created_at__gte=six_months_ago
        ).count()

        last_30 = access_events.filter(
            created_at__gte=thirty_days_ago
        ).count()

        previous_30 = access_events.filter(
            created_at__gte=sixty_days_ago,
            created_at__lt=thirty_days_ago
        ).count()

        growth_rate = 0
        if previous_30 > 0:
            growth_rate = round(
                ((last_30 - previous_30) / previous_30) * 100, 2
            )

        monthly_accesses = (
            access_events.filter(created_at__gte=six_months_ago)
            .annotate(month=TruncMonth("created_at"))
            .values("month")
            .annotate(total_clicks=Count("id"))
            .order_by("month")
        )

        monthly_labels = [
            entry["month"].strftime("%b/%Y")
            for entry in monthly_accesses
        ]

        monthly_data = [
            entry["total_clicks"]
            for entry in monthly_accesses
        ]

        top_clicked_urls = user_urls.filter(
            clicks__gt=0
        ).order_by("-clicks")[:10]

        top_urls_labels = [url.short_code for url in top_clicked_urls]
        top_urls_clicks = [url.clicks or 0 for url in top_clicked_urls]

        country_distribution = (
            access_events
            .exclude(country__isnull=True)
            .values("country")
            .annotate(total=Count("id"))
            .order_by("-total")[:10]
        )

        country_labels = [country["country"] for country in country_distribution]
        country_data = [country["total"] for country in country_distribution]

        device_distribution = (
            access_events
            .values("device_type")
            .annotate(total=Count("id"))
            .order_by("-total")
        )

        device_labels = [d["device_type"] for d in device_distribution]
        device_data = [d["total"] for d in device_distribution]

        browser_distribution = (
            access_events
            .exclude(browser__isnull=True)
            .values("browser")
            .annotate(total=Count("id"))
            .order_by("-total")[:5]
        )

        browser_labels = [b["browser"] for b in browser_distribution]
        browser_data = [b["total"] for b in browser_distribution]

        bot_stats = access_events.aggregate(
            humans=Count("id", filter=Q(is_bot=False)),
            bots=Count("id", filter=Q(is_bot=True)),
        )

        bot_labels = ["Humanos", "Bots"]
        bot_data = [
            bot_stats["humans"] or 0,
            bot_stats["bots"] or 0,
        ]

        context = {
            "user_links": user_urls,
            "recent_links": user_urls[:5],
            "total_links": total_urls,
            "total_accesses": total_access_events,
            "six_months_accesses": total_accesses_last_6_months,
            "growth_rate": growth_rate,

            "line_labels": monthly_labels,
            "line_data": monthly_data,

            "pie_labels": top_urls_labels,
            "pie_data": top_urls_clicks,
            
            "country_labels": country_labels,
            "country_data": country_data,
            "device_labels": device_labels,
            "device_data": device_data,
            "browser_labels": browser_labels,
            "browser_data": browser_data,
            "bot_labels": bot_labels,
            "bot_data": bot_data,
        }

        return render(request, "dashboard/home.html", context)


class UrlDelete(LoginRequiredMixin, View):
    def post(self, request, url_id: str):
        try:
            url_object = Url.objects.get(id=url_id, created_by=request.user)
            url_object.delete()
            return JsonResponse({"success": True, "message": "Link excluído com sucesso."})
        except Url.DoesNotExist:
            return JsonResponse(
                {"error": "Link não encontrado ou você não tem permissão."}, status=404
            )
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)


class UrlUpdate(LoginRequiredMixin, View):
    def post(self, request, url_id: str):
        try:
            data = json.loads(request.body)
            new_url = data.get("original_url")

            if not new_url:
                return JsonResponse({"error": "Campo original_url é obrigatório."}, status=400)

            url_object = Url.objects.get(id=url_id, created_by=request.user)
            url_object.original_url = new_url
            url_object.save()

            return JsonResponse({"success": True, "message": "URL atualizada com sucesso."})
        except Url.DoesNotExist:
            return JsonResponse(
                {"error": "Link não encontrado ou você não tem permissão."}, status=404
            )
        except json.JSONDecodeError:
            return JsonResponse({"error": "JSON inválido."}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)


class UserUrlsList(LoginRequiredMixin, ListView):
    model = Url
    template_name = "dashboard/all_urls_list.html"
    context_object_name = "links"
    login_url = "/account/login/"
    redirect_field_name = "next"
    paginate_by = 15

    def get_queryset(self):
        clicks_subquery = (
            AccessEvent.objects.filter(url=OuterRef("pk"))
            .values("url")
            .annotate(total_clicks=Count("id"))
            .values("total_clicks")[:1]
        )

        qs = Url.objects.filter(created_by=self.request.user).select_related("metadata").annotate(
            clicks=Subquery(clicks_subquery)
        )

        search = self.request.GET.get("q", "").strip()
        if search:
            qs = qs.filter(Q(original_url__icontains=search) | Q(short_code__icontains=search))

        min_clicks = self.request.GET.get("min_clicks")

        if min_clicks and min_clicks.isdigit():
            qs = qs.filter(clicks__gte=int(min_clicks))
        return qs.order_by("-created_at")
