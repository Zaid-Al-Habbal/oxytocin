from django.urls import path

from . import views

urlpatterns = [
    path(
        "",
        views.UserCreateDestroyView.as_view(),
        name="user-create-destroy",
    ),
    path(
        "logout/",
        views.LogoutView.as_view(),
        name="logout",
    ),
    path(
        "refresh-token/",
        views.CustomTokenRefreshView.as_view(),
        name="refresh-token",
    ),
    path(
        "change-password/",
        views.ChangePasswordView.as_view(),
        name="change-password",
    ),
    path(
        "images/",
        views.UserImageView.as_view(),
        name="user-image",
    ),
    path(
        "phone-verification/send/",
        views.UserPhoneVerificationSendView.as_view(),
        name="user-phone-verification-send",
    ),
    path(
        "phone-verification/",
        views.UserPhoneVerificationView.as_view(),
        name="user-phone-verification",
    ),
]
