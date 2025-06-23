from django import forms
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _

class CustomRegisterForm(forms.ModelForm):
    username = forms.CharField(
        label=_("Username"),
        widget=forms.TextInput(attrs={'placeholder': _("Your username")})
    )

    email = forms.CharField(
        label=_("E-mail address"),
        widget=forms.EmailInput(attrs={'placeholder': _("example@email.com")})
    )

    password = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput(attrs={'placeholder': _("Your secure password")})
    )

    confirm_password = forms.CharField(
        label=_("Confirm password"),
        widget=forms.PasswordInput(attrs={'placeholder': _("Confirm your password")})
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password')

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError(_("Passwords do not match."))

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class CustomLoginForm(forms.Form):
    identifier = forms.CharField(
        label=_("Username or Email"),
        widget=forms.TextInput(attrs={'placeholder': _("Username or Email")})
    )
    password = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput(attrs={'placeholder': _("Password")})
    )

    def clean(self):
        cleaned_data = super().clean()
        identifier = cleaned_data.get('identifier')
        password = cleaned_data.get('password')
        
        user = None

        if identifier and password:
            if '@' in identifier:
                try:
                    user_obj = User.objects.get(email__iexact=identifier)
                    username = user_obj.username
                    print(username)
                except User.DoesNotExist:
                    raise forms.ValidationError(
                        _("No user found with this email address.")
                    )
            else:
                username = identifier

            user = authenticate(username=username, password=password)
            print(user)
            if user is None:
                raise forms.ValidationError(
                    _("Invalid credentials. Please check your username/email and password.")
                )

        self.user = user
        return cleaned_data

    def get_user(self):
        return getattr(self, 'user', None)
