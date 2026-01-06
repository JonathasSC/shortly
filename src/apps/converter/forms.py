from django import forms
from django.utils.translation import gettext_lazy

from .models import Url


class UrlForm(forms.ModelForm):
    class Meta:
        model = Url
        fields = [
            'original_url',
            'is_direct',
        ]
        labels = {
            'original_url': gettext_lazy('Original URL'),
            'is_direct': gettext_lazy('Direct Link'),
        }
        widgets = {
            'original_url': forms.URLInput(attrs={
                'class': 'w-full p-2 border text-sm sm:text-md border-zinc-200 rounded focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': gettext_lazy('Type or Paste your URL here...')
            }),
            'is_direct': forms.CheckboxInput(attrs={
                'class': 'sr-only peer',
            })
        }
