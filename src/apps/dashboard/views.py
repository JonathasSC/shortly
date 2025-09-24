from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from apps.converter.models import Url, AccessEvent
from django.db.models import Sum

class DashboardHomeView(LoginRequiredMixin, View):
    login_url = '/account/login/'
    redirect_field_name = 'next'

    def get(self, request):
        # Todos os links criados pelo usuário logado
        user_links = Url.objects.filter(created_by=request.user).order_by('-created_at')

        # Total de links
        total_links = user_links.count()

        # Total de acessos (somando 'counter' de todos os AccessEvent dos links do usuário)
        total_accesses = AccessEvent.objects.filter(url__in=user_links).aggregate(total=Sum('counter'))['total'] or 0

        # Lista de links recentes com quantidade de acessos
        # Usando annotate para pegar os cliques por link
        from django.db.models import Sum as SumAgg
        recent_links = user_links.annotate(clicks=SumAgg('accessevent__counter')).order_by('-created_at')

        context = {
            "user_links": user_links,
            "total_links": total_links,
            "total_accesses": total_accesses,
            "recent_links": recent_links,
        }
        return render(request, 'dashboard/home.html', context)
