from django.urls import path

from . import views

urlpatterns = [
    path(
        "",
        views.UserCreateView.as_view(),
        name="user-create",
    ),
    path(
        "logout/",
        views.LogoutView.as_view(),
        name="login",
    ),
    path(
        "<int:pk>/",
        views.UserUpdateDestroyView.as_view(),
        name="user-update-destroy",
    ),
    path(
        "refresh-token/",
        views.CustomTokenRefreshView.as_view(),
        name="refresh-token",
    ),
    path('change-password/',
        ChangePasswordView.as_view(), 
        name='change-password'),
]
