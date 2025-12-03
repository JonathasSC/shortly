from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import (
    LoginView,
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import DeleteView, UpdateView
from django.views.generic.edit import CreateView

from apps.account.forms import CustomLoginForm, CustomRegisterForm, ProfileForm
from apps.account.models import User


class UserRegisterView(CreateView):
    form_class = CustomRegisterForm
    template_name = "account/register.html"
    success_url = reverse_lazy("login")


class UserLoginView(LoginView):
    template_name = "account/login.html"
    form_class = CustomLoginForm
    redirect_authenticated_user = True


class UserLogoutView(View):
    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        logout(request)
        return redirect("login")


class RecoveryView(PasswordResetView):
    template_name = "account/password_reset.html"
    email_template_name = "notification/email/password_reset.html"
    html_email_template_name = "notification/email/password_reset.html"
    subject_template_name = "account/password_reset_subject.txt"
    success_url = reverse_lazy("password_reset_done")


class RecoveryDoneView(PasswordResetDoneView):
    template_name = "account/password_reset_done.html"


class RecoveryConfirmView(PasswordResetConfirmView):
    template_name = "account/password_reset_confirm.html"
    success_url = reverse_lazy("password_reset_complete")


class RecoveryCompleteView(PasswordResetCompleteView):
    template_name = "account/password_reset_complete.html"


class UserProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = ProfileForm
    template_name = "account/profile_edit.html"
    success_url = reverse_lazy("profile_edit")

    def get_object(self, queryset=None):
        return self.request.user
    
class UserDeleteView(LoginRequiredMixin, DeleteView):
    model = User
    template_name = "account/profile_delete_confirm.html"
    success_url = reverse_lazy("login")

    def get_object(self, queryset=None):
        return self.request.user

    def delete(self, request, *args, **kwargs):
        logout(request)
        return super().delete(request, *args, **kwargs)