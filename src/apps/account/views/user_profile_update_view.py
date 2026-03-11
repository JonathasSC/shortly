from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as translate
from django.views.generic import UpdateView

from apps.account.forms.profile import ProfileForm
from apps.account.models import UserProfile


class UserProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = UserProfile
    form_class = ProfileForm
    template_name = "account/profile/profile.html"
    success_url = reverse_lazy("account:profile_edit")

    def get_object(self, queryset=None):
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        
        # DEBUG S3 RETRIEVAL
        print("\n--- S3 DEBUG START ---")
        print(f"User: {self.request.user.email} (ID: {self.request.user.id})")
        if profile.avatar:
            print(f"Avatar field value: {profile.avatar.name}")
            try:
                print(f"Avatar URL: {profile.avatar.url}")
                exists = profile.avatar.storage.exists(profile.avatar.name)
                print(f"File exists on S3: {exists}")
                if exists:
                    print(f"File size: {profile.avatar.size} bytes")
            except Exception as e:
                print(f"Error accessing S3: {str(e)}")
        else:
            print("No avatar associated with this profile.")
        print("--- S3 DEBUG END ---\n")
        
        return profile

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, translate("Profile updated successfully."))
        return super().form_valid(form)
