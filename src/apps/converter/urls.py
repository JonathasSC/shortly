from django.urls import path

from .views import ConfirmRedirectView, HomeView, MiddleView, QrCodeImageView, UrlDetailView

app_name = "converter"

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('url/<str:short_code>/', UrlDetailView.as_view(), name='url-detail'),
    path('url/<str:short_code>/qr.png', QrCodeImageView.as_view(), name='url-qr'),
    path('redirect/confirm/', ConfirmRedirectView.as_view(), name='confirm-redirect'),
    path('<str:short_code>/', MiddleView.as_view(), name='url-redirect'),
]
