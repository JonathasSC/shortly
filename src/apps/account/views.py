from django.urls import reverse_lazy
from .forms import CustomRegisterForm, CustomLoginForm
from django.views.generic.edit import CreateView, FormView
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth import login, logout
from django.shortcuts import redirect
from django.views import View

class RegisterView(FormView):
    form_class = CustomRegisterForm
    template_name = 'account/register.html'


class LoginView(FormView):
    form_class = CustomLoginForm
    template_name = 'account/login.html'
    success_url = reverse_lazy('home')
    
    def form_valid(self, form):
        user = form.get_user()
        if user is not None:
            login(self.request, user)
        return super().form_valid(form)
    
class LogoutView(View):
    def get(self, request, *args, **kwargs):
        logout(request)
        return redirect('login') 