from django import forms
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy

from .models import UserProfile


class CustomRegisterForm(forms.ModelForm):
    password = forms.CharField(
        label=gettext_lazy("Password"),
        widget=forms.PasswordInput()
    )
    confirm_password = forms.CharField(
        label=gettext_lazy("Confirm password"),
        widget=forms.PasswordInput()
    )

    image = forms.ImageField(
        label=gettext_lazy("Profile Image"),
        required=False
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password')

    def clean(self):
        cleaned_data = super(CustomRegisterForm, self).clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password != confirm_password:
            raise forms.ValidationError(
                gettext_lazy("Passwords do not match")
            )

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])

        if commit:
            user.save()
            UserProfile.objects.create(
                user=user,
                image=self.cleaned_data.get('image')
            )

        return user
