import secrets
from datetime import timedelta

from django.contrib import messages
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.timezone import now
from django.views import View

from apps.converter.models import AccessEvent, Url
from apps.converter.utils import UserRequestUtil

from .forms import UrlForm

user_request_util = UserRequestUtil()


class MiddleView(View):
    def get(self, request, short_code) -> HttpResponse:
        url = get_object_or_404(Url, short_code=short_code)
        token = secrets.token_urlsafe(16)
        timestamp = timezone.now().timestamp()
        ip_address = user_request_util.get_client_ip(request)

        AccessEvent.objects.create(
            url=url,
            ip_address=ip_address
        )

        request.session[f"token_{token}"] = {
            "timestamp": timestamp,
            "target_url": url.original_url
        }

        return render(request, 'converter/middle.html', {
            "redirect_url": reverse("confirm_redirect") + f"?token={token}",
        })


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
            return render(request, 'converter/middle.html', {
                "redirect_url": reverse("confirm_redirect") + f"?token={token}",
                "remaining": remaining,
            })
        
        del request.session[f"token_{token}"]
        return redirect(target_url)


class HomeView(View):
    def get(self, request):
        form = UrlForm()
        return render(request, 'converter/home.html', {
            'form': form,
        })

    def post(self, request):
        form = UrlForm(request.POST)

        short_url = None
        existing_url = None
        client_ip = user_request_util.get_client_ip(request)

        if not getattr(request, 'user', None) or not request.user.is_authenticated:

            today_start = now().replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = today_start + timedelta(days=1)

            count_today = Url.objects.filter(
                created_by_ip=client_ip,
                created_at__range=(today_start, today_end)
            ).count()

            MAX_IP_PER_DAY = 5
            if count_today >= MAX_IP_PER_DAY:
                messages.error(request, mark_safe('''
                    <p class="text-center bg-yellow-100 w-full max-w-lg px-4 py-2 w-80 rounded text-yellow-600">
                        Você atingiu o limite de 5 links por dia. Tente novamente amanhã ou faça login para continuar.
                    </p>
                '''))
                return redirect('home')

        if form.is_valid():
            url_object = form.save(commit=False)

            if getattr(request, 'user', None) and request.user.is_authenticated:
                existing_url = Url.objects.filter(
                    original_url=url_object.original_url,
                    created_by=request.user
                ).first()
            else:
                existing_url = Url.objects.filter(
                    original_url=url_object.original_url,
                    created_by=None,
                    created_by_ip=client_ip
                ).first()

            if existing_url:
                url_object = existing_url
            else:
                if request.user.is_authenticated:
                    url_object.created_by = request.user
                    url_object.created_by_ip = None
                else:
                    url_object.created_by = None
                    url_object.created_by_ip = client_ip
                url_object.save()

            short_url = request.build_absolute_uri(
                f'/{url_object.short_code}/')
            
            html_message = render_to_string('converter/includes/success_message.html', {
                'short_url': short_url
            })
            messages.success(request, mark_safe(html_message))

            return redirect('home')

        messages.error(
            request, 'Erro ao criar o link. Verifique o formulário.')
        return redirect('home')
