from django.urls import path

from . import views


urlpatterns = [
    path(
        "password-reset/",
        views.PasswordResetView.as_view(),
        name="admin_password_reset",
    ),
    path(
        "password-reset/confirm/",
        views.PasswordResetConfirmView.as_view(),
        name="admin_password_reset_confirm",
    ),
    path(
        "password-reset/complete/",
        views.PasswordResetCompleteView.as_view(),
        name="admin_password_reset_complete",
    ),
]
