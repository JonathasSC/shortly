from django.urls import path

from apps.account.views import (
    UserLogoutView,
    RecoveryCompleteView,
    RecoveryConfirmView,
    RecoveryDoneView,
    RecoveryView,
    UserRegisterView,
    UserLoginView,
)

urlpatterns = [
    path("login/", UserLoginView.as_view(), name="login"),
    path("register/", UserRegisterView.as_view(), name="register"),
    path("logout/", UserLogoutView.as_view(), name="logout"),

    # Recovery
    path(
        "recovery/",
        RecoveryView.as_view(),
        name="recovery"
    ),
    path(
        "recovery/done/",
        RecoveryDoneView.as_view(),
        name="password_reset_done"
    ),
    path(
        "recovery/confirm/<uidb64>/<token>/",
        RecoveryConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "recovery/complete/",
        RecoveryCompleteView.as_view(),
        name="password_reset_complete"
    ),
]
