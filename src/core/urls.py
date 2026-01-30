from django.contrib import admin
from django.urls import include, path

from apps.common.views import NotFoundView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("i18n/", include("django.conf.urls.i18n")),
    path("info/", include("apps.institutional.urls")),
    path("account/", include("apps.account.urls")),
    path("dashboard/", include("apps.monitor.urls")),
    path("buy/", include("apps.billing.urls")),
    path("manager/", include("apps.manager.urls")),
    path("", include("apps.converter.urls")),
    path("", include("apps.common.urls")),

]

handler404 = NotFoundView.as_view()
