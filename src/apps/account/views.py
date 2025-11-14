from django.conf import settings
from django.contrib.auth import logout
from django.contrib.auth.views import (
    LoginView,
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic.edit import CreateView

from .forms import CustomLoginForm, CustomRegisterForm


class RegisterView(CreateView):
    form_class = CustomRegisterForm
    template_name = "account/register.html"
    success_url = reverse_lazy("login")


class UserLoginView(LoginView):
    template_name = "account/login.html"
    form_class = CustomLoginForm
    redirect_authenticated_user = True
    success_url = reverse_lazy("apps.converter:home")


class LogoutView(View):
    def get(self, request, *args, **kwargs):
        logout(request)
        return redirect("login")


class RecoveryView(PasswordResetView):
    template_name = "account/password_reset.html"
    email_template_name = "notification/email/password_reset_email.html"
    html_email_template_name = "notification/email/password_reset_email.html"
    subject_template_name = "account/password_reset_subject.txt"
    success_url = reverse_lazy("password_reset_done")

    def form_valid(self, form):
        form.save(from_email=settings.DEFAULT_FROM_EMAIL, request=self.request, use_https=False)
        return super().form_valid(form)


class RecoveryDoneView(PasswordResetDoneView):
    template_name = "account/password_reset_done.html"


class RecoveryConfirmView(PasswordResetConfirmView):
    template_name = "account/password_reset_confirm.html"
    success_url = reverse_lazy("password_reset_complete")


class RecoveryCompleteView(PasswordResetCompleteView):
    template_name = "account/password_reset_complete.html"
