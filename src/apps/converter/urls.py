from django.urls import path

from .views import ConfirmRedirectView, HomeView, MiddleView

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('<str:short_code>/', MiddleView.as_view(), name='url-redirect'),
    path('redirect/confirm/', ConfirmRedirectView.as_view(), name='confirm_redirect'),
]
