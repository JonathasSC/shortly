from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', include('apps.converter.urls')),
    path('info/', include('apps.institutional.urls')),
    path('account/', include('apps.account.urls')),
    path('dashboard/', include('apps.dashboard.urls')),
    path('buy/', include('apps.billing.urls')),
]
