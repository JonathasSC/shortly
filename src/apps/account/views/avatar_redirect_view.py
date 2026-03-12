from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views import View
from apps.account.models import UserProfile


class AvatarRedirectView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        profile = get_object_or_404(UserProfile, user_id=kwargs.get('user_id'))
        
        # Controle de acesso no Django: apenas o próprio dono vê a imagem
        if profile.user != request.user and not request.user.is_superuser:
            return HttpResponseForbidden("Você não tem permissão para visualizar esta imagem.")
            
        if not profile.avatar:
            # Retorna o placeholder padrão via redirect simples
            return HttpResponseRedirect('/static/images/default-avatar.png')
            
        # IMPORTANTE: Usamos HttpResponseRedirect diretamente com profile.avatar.url
        # Isso evita que o Django tente escapar os caracteres da assinatura do S3 novamente.
        return HttpResponseRedirect(profile.avatar.url)
