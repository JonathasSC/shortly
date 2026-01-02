from datetime import timedelta

from axes.decorators import axes_dispatch
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import (
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic.edit import CreateView

from apps.account.forms.auth import CustomLoginForm, CustomRegisterForm
from apps.account.models import UserDeletionSchedule

User = get_user_model()


@method_decorator(axes_dispatch, name="dispatch")
class UserRegisterView(CreateView):
    form_class = CustomRegisterForm
    template_name = "account/auth/register.html"
    success_url = reverse_lazy("login")


class UserLoginView(View):
    template_name = "account/auth/login.html"
    form_class = CustomLoginForm

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("converter:home")
        return render(request, self.template_name, {"form": self.form_class()})

    def post(self, request):
        form = self.form_class(request.POST)

        if not form.is_valid():
            return render(
                request,
                self.template_name,
                {"form": form},
                status=400,
            )

        username = form.cleaned_data["username"]
        password = form.cleaned_data["password"]

        try:
            user_obj = User.objects.get(username=username)
        except User.DoesNotExist:
            messages.error(request, _(
                "Não foi possível entrar. Verifique seu usuário e senha."))
            return render(
                request,
                self.template_name,
                {"form": self.form_class()},
                status=400,
            )

        if not user_obj.is_active:
            messages.error(
                request,
                _("Sua conta foi encerrada. "
                  "Se acredita que isso é um engano, entre em contato com o suporte.")
            )
            return render(
                request,
                self.template_name,
                {"form": self.form_class()},
                status=403,
            )

        user = authenticate(
            request=request,
            username=username,
            password=password,
        )

        if user is None:
            messages.error(
                request,
                _("Usuário ou senha inválidos.")
            )

            return render(
                request,
                self.template_name,
                {"form": self.form_class()},
                status=400,
            )

        login(request, user)

        return redirect("converter:home")


class UserLogoutView(View):
    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        logout(request)
        return redirect("account:login")


class RecoveryView(PasswordResetView):
    template_name = "account/auth/password_reset.html"
    email_template_name = "notification/email/password_reset.html"
    html_email_template_name = "notification/email/password_reset.html"
    subject_template_name = "account/auth/password_reset_subject.txt"
    success_url = reverse_lazy("password_reset_done")


class RecoveryDoneView(PasswordResetDoneView):
    template_name = "account/auth/password_reset_done.html"


class RecoveryConfirmView(PasswordResetConfirmView):
    template_name = "account/auth/password_reset_confirm.html"
    success_url = reverse_lazy("password_reset_complete")


class RecoveryCompleteView(PasswordResetCompleteView):
    template_name = "account/auth/password_reset_complete.html"


class DeactivateAccount(LoginRequiredMixin, View):
    def post(self, request):
        user = request.user
        user.is_active = False
        user.save()

        UserDeletionSchedule.objects.update_or_create(
            user=user,
            defaults={
                "scheduled_for": timezone.now() + timedelta(days=30)
            }
        )

        return redirect("account:logout")
