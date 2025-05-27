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
]
