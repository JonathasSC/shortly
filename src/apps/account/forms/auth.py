from django import forms
from django.utils.translation import gettext_lazy as translate

from apps.account.models import User
from apps.account.utils import AuthenticationUtils


class CustomRegisterForm(forms.ModelForm):
    username = forms.CharField(
        label=translate("Username"),
        widget=forms.TextInput(attrs={
            'placeholder': translate("Your username"),
            'class': 'w-full text-sm sm:text-md p-2 border border-zinc-200 rounded focus:outline-none focus:ring-2 focus:ring-blue-500',
        })
    )

    email = forms.CharField(
        label=translate("E-mail address"),
        widget=forms.EmailInput(attrs={
            'placeholder': translate("example@email.com"),
            'class': 'w-full text-sm sm:text-md p-2 border border-zinc-200 rounded focus:outline-none focus:ring-2 focus:ring-blue-500',
        })
    )

    password = forms.CharField(
        label=translate("Password"),
        widget=forms.PasswordInput(attrs={
            'placeholder': translate("Your secure password"),
            'class': 'w-full text-sm sm:text-md p-2 border border-zinc-200 rounded focus:outline-none focus:ring-2 focus:ring-blue-500',
        })
    )

    confirm_password = forms.CharField(
        label=translate("Confirm password"),
        widget=forms.PasswordInput(attrs={
            'placeholder': translate("Confirm your password"),
            'class': 'w-full text-sm sm:text-md p-2 border border-zinc-200 rounded focus:outline-none focus:ring-2 focus:ring-blue-500',
        })
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password')

    def clean_password(self):
        password = self.cleaned_data.get('password')
        try:
            auth_utils: AuthenticationUtils = AuthenticationUtils()
            auth_utils.password_validation(password)
        except Exception as error:
            raise forms.ValidationError(error)
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError(translate("Passwords do not match."))

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class CustomLoginForm(forms.Form):
    username = forms.CharField(
        label=translate("Username"),
        widget=forms.TextInput(attrs={
            'placeholder': translate("Seu nome de usuário"),
            'class': 'w-full text-sm sm:text-md p-2 border border-zinc-200 rounded focus:outline-none focus:ring-2 focus:ring-blue-500',
        })
    )

    password = forms.CharField(
        label=translate("Password"),
        widget=forms.PasswordInput(attrs={
            'placeholder': translate("Sua senha"),
            'class': 'w-full text-sm sm:text-md p-2 border border-zinc-200 rounded focus:outline-none focus:ring-2 focus:ring-blue-500',
        })
    )
