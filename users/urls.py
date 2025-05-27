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
        name="logout",
    ),
    path(
        "<int:pk>/",
        views.UserDestroyView.as_view(),
        name="user-destroy",
    ),
    path(
        "refresh-token/",
        views.CustomTokenRefreshView.as_view(),
        name="refresh-token",
    ),
    path('change-password/',
        views.ChangePasswordView.as_view(), 
        name='change-password'),
]
