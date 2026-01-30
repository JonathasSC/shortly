from django.urls import path

from apps.monitor.views import DashboardHomeView, UrlDelete, UrlUpdate, UserUrlsList

urlpatterns = [
    path('', DashboardHomeView.as_view(), name='dashboard_home'),
    path('urls/', UserUrlsList.as_view(), name='user_url_list'),
    path('url/<uuid:url_id>/update/', UrlUpdate.as_view(), name='update_link'),
    path('url/<uuid:url_id>/delete/', UrlDelete.as_view(), name='delete_link'),
]
