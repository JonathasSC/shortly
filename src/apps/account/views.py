from django.shortcuts import render
from django.urls import reverse_lazy
from .forms import CustomRegisterForm
from django.views import View
from django.views.generic.edit import CreateView
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.models import User


class RegisterView(SuccessMessageMixin, CreateView):
    form_class = CustomRegisterForm
    template_name = 'account/register.html'
    success_url = reverse_lazy('login')
    success_message = "Your profile was created successfully"
