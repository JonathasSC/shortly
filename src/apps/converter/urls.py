from django.urls import path
from .views import HomeView, MiddleView

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('<str:short_code>/', MiddleView.as_view(), name='url-redirect'),
]
