from django.urls import path

from apps.account.views import (
    LogoutView,
    RecoveryCompleteView,
    RecoveryConfirmView,
    RecoveryDoneView,
    RecoveryView,
    RegisterView,
    UserLoginView,
)

urlpatterns = [
    path("login/", UserLoginView.as_view(), name="login"),
    path("register/", RegisterView.as_view(), name="register"),
    path("logout/", LogoutView.as_view(), name="logout"),
    # Recovery
    path("recovery/", RecoveryView.as_view(), name="recovery"),
    path("recovery/done/", RecoveryDoneView.as_view(), name="password_reset_done"),
    path(
        "recovery/confirm/<uidb64>/<token>/",
        RecoveryConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path("recovery/complete/", RecoveryCompleteView.as_view(), name="password_reset_complete"),
]
