from django.utils.translation import gettext_lazy as _
from django.contrib.auth import authenticate

from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import CustomUser as User


class DoctorLoginSerializer(serializers.Serializer):
    phone = serializers.CharField(write_only=True)
    password = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
        help_text="Password must meet the validation rules (min length=8, has both lowercase and uppercase latters, number, special character, not common, not similar to user's attributes ).",
    )
    access_token = serializers.CharField(read_only=True)
    refresh_token = serializers.CharField(read_only=True)
    expires_in = serializers.IntegerField(read_only=True)

    def validate(self, data):
        phone = data.get("phone")
        password = data.get("password")
        user = authenticate(phone=phone, password=password)
        if user is None or user.role != User.Role.DOCTOR or user.deleted_at is not None:
            raise serializers.ValidationError(_("Invalid credentials!"))
        if not user.is_verified_phone:
            raise serializers.ValidationError(
                _("Please, verify your phone number first")
            )
        refresh_token = RefreshToken.for_user(user)
        access_token = refresh_token.access_token
        expires_in = int(access_token.lifetime.total_seconds())
        return {
            "access_token": str(access_token),
            "refresh_token": str(refresh_token),
            "expires_in": expires_in,
        }
