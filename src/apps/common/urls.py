from django.urls import path

from apps.common.views import NotFoundView

app_name = "common"

urlpatterns = [
    path("notfound/", NotFoundView.as_view(), name="notfound"),
]
