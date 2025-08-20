from django.utils.translation import gettext_lazy as _
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django import forms
from unfold.forms import UnfoldAdminPasswordInput

from .models import CustomUser


class CustomUserCreationForm(UserCreationForm):

    password1 = forms.CharField(
        label=_("Password"),
        min_length=8,
        widget=UnfoldAdminPasswordInput(),
        required=True,
    )
    password2 = forms.CharField(
        label=_("Password confirmation"),
        widget=UnfoldAdminPasswordInput(),
        required=True,
    )

    class Meta:
        model = CustomUser
        fields = (
            "first_name",
            "last_name",
            "phone",
            "is_verified_phone",
            "email",
            "is_verified_email",
            "image",
            "gender",
            "birth_date",
            "role",
            "is_active",
            "is_staff",
            "is_superuser",
        )


class CustomUserChangeForm(UserChangeForm):

    class Meta:
        model = CustomUser
        fields = (
            "first_name",
            "last_name",
            "phone",
            "is_verified_phone",
            "email",
            "is_verified_email",
            "image",
            "gender",
            "birth_date",
            "role",
            "is_active",
            "is_staff",
            "is_superuser",
            "deleted_at",
        )
