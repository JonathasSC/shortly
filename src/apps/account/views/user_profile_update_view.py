from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import UpdateView

from apps.account.forms.profile import ProfileForm
from apps.account.models import User


class UserProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = ProfileForm
    template_name = "account/profile/profile.html"
    success_url = reverse_lazy("account:profile_edit")

    def get_object(self, queryset=None):
        return self.request.user
