from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path('admin/', admin.site.urls),

    path('', include('apps.converter.urls')),
    path('account/', include('apps.account.urls')),
    path('dashboard', include('apps.dashboard.urls')),
]
