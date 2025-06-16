from django.views.generic.base import RedirectView
from django.views import View
from django.shortcuts import get_object_or_404
from .models import Url
from django.shortcuts import render
from .forms import UrlForm
from typing import Optional


class RedirectView(RedirectView):
    permanent = False
    query_string = True

    def get_redirect_url(self, **kwargs):
        url = get_object_or_404(Url, short_code=kwargs["short_code"])
        return url.original_url


class HomeView(View):
    def get(self, request):
        url_form: UrlForm = UrlForm()
        return render(request, 'converter/home.html', {'url_form': url_form})

    def post(self, request):
        url_form: UrlForm = UrlForm(request.POST)
        short_url: Optional[str] = None

        if url_form.is_valid():
            url_object = url_form.save(commit=False)
            url_object.save()

            short_url = request.build_absolute_uri(
                f'/{url_object.short_code}/'
            )

        context = {
            'url_form': url_form,
            'short_url': short_url
        }
        print(context)
        return render(request, 'converter/home.html', context)
