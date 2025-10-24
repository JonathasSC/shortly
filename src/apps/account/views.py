from django.contrib.auth import login, logout
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic.edit import CreateView
from django.contrib.auth.views import LoginView

from .forms import CustomLoginForm, CustomRegisterForm


class RegisterView(CreateView):
    form_class = CustomRegisterForm
    template_name = 'account/register.html'
    success_url = reverse_lazy('login')


class UserLoginView(LoginView):
    template_name = 'account/login.html'
    form_class = CustomLoginForm
    redirect_authenticated_user = True
    success_url = reverse_lazy('apps.converter:home')


class LogoutView(View):
    def get(self, request, *args, **kwargs):
        logout(request)
        return redirect('login')
