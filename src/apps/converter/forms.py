from django import forms
from .models import Url
from django.utils.translation import gettext_lazy


class UrlForm(forms.ModelForm):
    class Meta:
        model = Url
        fields = [
            'original_url'
        ]
        labels = {
            'original_url': gettext_lazy('Your URL')
        }
        widgets = {
            'original_url': forms.URLInput(attrs={
                'class': 'w-full p-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': gettext_lazy('Type or Paste your URL here...')
            })
        }
