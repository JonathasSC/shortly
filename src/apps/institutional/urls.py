from django.urls import path

from apps.institutional.views import AboutUsView, PrivacyPolicy

urlpatterns = [
    path('about-us/', AboutUsView.as_view(), name='about-us'),
    path('privacy-policy/', PrivacyPolicy.as_view(), name='privacy-policy'),
]