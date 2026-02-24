from django import forms
from django.utils.translation import gettext_lazy

from .models import Url


class UrlForm(forms.ModelForm):
    is_direct = forms.BooleanField(
        required=False,
        label=gettext_lazy("Direct Link"),
        widget=forms.CheckboxInput(attrs={
            "class": "sr-only peer",
        }),
    )

    is_permanent = forms.BooleanField(
        required=False,
        label=gettext_lazy("Permanent Link"),
        widget=forms.CheckboxInput(attrs={
            "class": "sr-only peer",
        }),
    )

    class Meta:
        model = Url
        fields = [
            "original_url",
        ]
        labels = {
            "original_url": gettext_lazy("Original URL"),
        }
        widgets = {
            "original_url": forms.URLInput(attrs={
                "class": "w-full p-2 border text-sm sm:text-md border-zinc-200 rounded "
                         "focus:outline-none focus:ring-2 focus:ring-blue-500",
                "placeholder": gettext_lazy("Type or Paste your URL here..."),
            }),
        }