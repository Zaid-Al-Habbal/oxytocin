from django.utils.translation import gettext_lazy as _
from django.contrib.auth import authenticate

from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken


class LoginPatientSerializer(serializers.Serializer):
    phone = serializers.CharField(write_only=True)
    password = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
        help_text="Password must meet the validation rules (min length=8, has both lowercase and uppercase latters, number, special character, not common, not similar to user's attributes ).",
    )
    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)

    def validate(self, data):
        phone = data.get("phone")
        password = data.get("password")

        user = authenticate(phone=phone, password=password)

        if user is None:
            raise serializers.ValidationError(_("Invalid credentials"))

        if user.role != "patient":
            raise serializers.ValidationError(_("Only patients can log in here."))

        if not user.is_verified_phone:
            raise serializers.ValidationError(
                _("Please, verify your phone number first")
            )

        refresh = RefreshToken.for_user(user)

        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }
