import secrets
from datetime import timedelta

from django.contrib import messages
from django.db import models
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.views import View

from apps.billing.models import UserWallet, WalletTransaction
from apps.converter.forms import UrlForm
from apps.converter.models import AccessEvent, Url
from apps.converter.utils import UserRequestUtil
from apps.notification.models import Announcement

user_request_util = UserRequestUtil()


class MiddleView(View):
    def get(self, request, short_code) -> HttpResponse:
        url = get_object_or_404(Url, short_code=short_code)
        token = secrets.token_urlsafe(16)
        timestamp = timezone.now().timestamp()
        ip_address = user_request_util.get_client_ip(request)

        AccessEvent.objects.create(url=url, ip_address=ip_address)

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

    def __debit_user_wallet(self, user):
        wallet, created = UserWallet.objects.get_or_create(user=user)

        if wallet.balance < 1:
            return False

        WalletTransaction.objects.create(
            wallet=wallet,
            transaction_type=WalletTransaction.TransactionType.DEBIT,
            amount=1,
            source="URL shortening",
        )
        return True

    def __create_short_url(self, url_object, user=None, client_ip=None):
        url_object.created_by = user
        url_object.created_by_ip = client_ip
        url_object.save()

        return url_object

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
        create_new = request.POST.get("create_new", "false") == "true"
        user = request.user

        if not form.is_valid():
            messages.error(request, "Erro ao criar o link. Verifique o formulário.")
            return redirect("home")

        url_object = form.save(commit=False)

        if not user.is_authenticated:
            MAX_IP_PER_DAY = 5
            today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = today_start + timedelta(days=1)

            count_today = Url.objects.filter(
                created_by_ip=client_ip, created_at__range=(today_start, today_end)
            ).count()

            if count_today >= MAX_IP_PER_DAY:
                messages.error(
                    request,
                    mark_safe("""
                    <p class="text-center bg-yellow-100 px-4 py-2 w-full rounded text-yellow-600">
                        Você atingiu o limite de 5 links por dia. Tente novamente amanhã ou faça login para continuar.
                    </p>
                """),
                )
                return redirect("home")

        existing_url = self.__get_existing_url(url_object, request.user, client_ip)

        if existing_url and not create_new:
            messages.info(
                request,
                mark_safe(f'''
                    <div class="existing-url-message" data-original-url="{existing_url.original_url}"></div>
                '''),
            )
            return redirect("home")

        if user and not self.__debit_user_wallet(user):
            messages.error(
                request,
                mark_safe("""
                <p class="text-center bg-red-100 w-full max-w-lg px-4 py-2 w-80 rounded text-red-600">
                    Saldo insuficiente! Adicione mais coins para encurtar mais URL's
                </p>
                """),
            )
            return redirect("home")

        created_url = self.__create_short_url(url_object, None, client_ip)
        short_url = request.build_absolute_uri(f"/{created_url.short_code}/")

        html_message = render_to_string(
            "converter/includes/success_message.html", {"short_url": short_url}
        )
        messages.success(request, mark_safe(html_message))
        return redirect("home")

    # def post(self, request):
    #     form = UrlForm(request.POST)
    #     client_ip = user_request_util.get_client_ip(request)
    #     create_new = request.POST.get("create_new", "false") == "true"
    #     user = request.user
    #     user_is_authenticated = user.is_authenticated

    #     if not form.is_valid():
    #         messages.error(request, "Erro ao criar o link. Verifique o formulário.")
    #         return redirect("home")

    #     url_object = form.save(commit=False)

    #     if user.is_authenticated:
    #         existing_url = self.__get_existing_url(url_object, request.user, client_ip)

    #         if existing_url and not create_new:
    #             messages.info(
    #                 request,
    #                 mark_safe(f'''
    #                 <div class="existing-url-message" data-original-url="{existing_url.original_url}"></div>
    #             '''),
    #             )
    #             return redirect("home")

    #         if user and not self.__debit_user_wallet(user):
    #             messages.error(
    #                 request,
    #                 mark_safe("""
    #                 <p class="text-center bg-red-100 w-full max-w-lg px-4 py-2 w-80 rounded text-red-600">
    #                     Saldo insuficiente! Adicione mais coins para encurtar mais URL's
    #                 </p>
    #             """),
    #             )
    #             return redirect("home")

    #         created_url = self.__create_short_url(url_object, user, client_ip)
    #         short_url = request.build_absolute_uri(f"/{created_url.short_code}/")

    #         html_message = render_to_string(
    #             "converter/includes/success_message.html", {"short_url": short_url}
    #         )

    #         messages.success(request, mark_safe(html_message))
    #         return redirect("home")

    #     today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    #     today_end = today_start + timedelta(days=1)

    #     count_today = Url.objects.filter(
    #         created_by_ip=client_ip, created_at__range=(today_start, today_end)
    #     ).count()

    #     MAX_IP_PER_DAY = 5
    #     if count_today >= MAX_IP_PER_DAY:
    #         messages.error(
    #             request,
    #             mark_safe("""
    #             <p class="text-center bg-yellow-100 px-4 py-2 w-full rounded text-yellow-600">
    #                 Você atingiu o limite de 5 links por dia. Tente novamente amanhã ou faça login para continuar.
    #             </p>
    #         """),
    #         )
    #         return redirect("home")

    #     created_url = self.__create_short_url(url_object, None, client_ip)
    #     short_url = request.build_absolute_uri(f"/{created_url.short_code}/")

    #     html_message = render_to_string(
    #         "converter/includes/success_message.html", {"short_url": short_url}
    #     )
    #     messages.success(request, mark_safe(html_message))
    #     return redirect("home")
