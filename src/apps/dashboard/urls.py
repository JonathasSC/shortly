from django.urls import path

from apps.dashboard.views import DashboardHomeView, UrlDelete, UrlUpdate, UserUrlsList

urlpatterns = [
    path('', DashboardHomeView.as_view(), name='dashboard-home'),
    path('urls/', UserUrlsList.as_view(), name='user-url-list'),
    path('url/<uuid:url_id>/update/', UrlUpdate.as_view(), name='update_link'),
    path('url/<uuid:url_id>/delete/', UrlDelete.as_view(), name='delete_link'),
]
