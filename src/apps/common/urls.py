from django.urls import path
from apps.common.views import NotFoundView

urlpatterns = [
    path("notfound/", NotFoundView.as_view(), name="notfound"),
]
