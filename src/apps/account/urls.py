from django.urls import path

from apps.account.views.auth import (
    DeactivateAccount,
    RecoveryCompleteView,
    RecoveryConfirmView,
    RecoveryDoneView,
    RecoveryView,
    UserLoginView,
    UserLogoutView,
    UserRegisterView,
)
from apps.account.views.profile import (
    UserDeleteView,
    UserProfileUpdateView,
)

app_name = "account"

urlpatterns = [
    path("login/", UserLoginView.as_view(), name="login"),
    path("register/", UserRegisterView.as_view(), name="register"),
    path("logout/", UserLogoutView.as_view(), name="logout"),

    # Profile
    path('profile/delete', UserDeleteView.as_view(), name='profile_delete'),
    path('profile/edit', UserProfileUpdateView.as_view(), name='profile_edit'),
    path("deactivate/", DeactivateAccount.as_view(), name="profile_deactivate"),

    # Recovery
    path("recovery/", RecoveryView.as_view(), name="recovery"),
    path("recovery/done/", RecoveryDoneView.as_view(), name="password_reset_done"),
    path(
        "recovery/confirm/<uidb64>/<token>/",
        RecoveryConfirmView.as_view(),
        name="recovery_confirm",
    ),
    path("recovery/complete/", RecoveryCompleteView.as_view(),
         name="password_reset_complete"),
]
