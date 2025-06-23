from django.views.generic.base import RedirectView
from django.views import View
from .models import Url
from django.shortcuts import render, redirect
from .forms import UrlForm
from apps.converter.utils import UserRequestUtil
from django.utils.timezone import now
from datetime import timedelta
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.utils.safestring import mark_safe

user_request_util = UserRequestUtil()

class RedirectView(RedirectView):
    permanent = False
    query_string = True

    def get_redirect_url(self, **kwargs):
        url = get_object_or_404(Url, short_code=kwargs["short_code"])
        return url.original_url
    
    
class HomeView(View):
    def get(self, request):
        url_form = UrlForm()
        return render(request, 'converter/home.html', {
            'url_form': url_form,
        })

    def post(self, request):
        url_form = UrlForm(request.POST)
        
        short_url = None
        existing_url = None


        if not request.user.is_authenticated:
            client_ip = user_request_util.get_client_ip(request)

            today_start = now().replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = today_start + timedelta(days=1)

            count_today = Url.objects.filter(
                created_by_ip=client_ip,
                created_at__range=(today_start, today_end)
            ).count()

            MAX_IP_PER_DAY = 5
            if count_today >= MAX_IP_PER_DAY:
                messages.error(request, mark_safe(f'''
                    <p class="text-center bg-yellow-100 px-4 py-2 w-80 rounded text-yellow-600">
                        Você atingiu o limite de 5 links por dia. Tente novamente amanhã ou faça login para continuar.
                    </p>
                '''))
                return redirect('home')

        if url_form.is_valid():
            url_object = url_form.save(commit=False)

            if request.user.is_authenticated:
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

            short_url = request.build_absolute_uri(f'/{url_object.short_code}/')
            
            messages.success(request, mark_safe(f'''
            <div id="shortUrlWrapper" class="flex flex-col gap-2 align-center justify-center">
                <p class="text-center">URL encurtada:</p>
                  
                <div class="flex gap-2">
                    <a href="{short_url}" id="shortUrlLink" target="_blank" class="underline rounded px-4 py-2 bg-gray-100 text-center text-blue-700">{short_url}</a>
                    <button id="copyButton" class="bg-gray-100 px-4 py-2 rounded flex items-center text-sm text-blue-600">
                        <span class="material-symbols-outlined text-base">
                            content_copy
                        </span>
                        <p id="copyButtonLabel">Copiar</p>
                    </button>
                </div>                              
                
            </div>
            '''))            
            
            return redirect('home')

        messages.error(request, 'Erro ao criar o link. Verifique o formulário.')
        return redirect('home')