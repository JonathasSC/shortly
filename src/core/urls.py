from django.contrib import admin
from django.urls import include, path

from apps.common.views import NotFoundView

urlpatterns = [
    path('admin/', admin.site.urls),

    path('info/', include('apps.institutional.urls')),
    path('account/', include('apps.account.urls')),
    path('dashboard/', include('apps.dashboard.urls')),
    path('buy/', include('apps.billing.urls')),

    path('', include('apps.converter.urls')),

    path('notfound/', include('apps.common.urls')),
]


handler404 = NotFoundView.as_view()
