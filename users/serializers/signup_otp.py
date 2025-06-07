from django.utils.translation import gettext_lazy as _
from django.conf import settings

from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import CustomUser as User
from users.services import OTPService
from users.tasks import send_sms


SIGNUP_KEY = "signup:user:%(user)s"
SIGNUP_MESSAGE = "🩺 Welcome to Oxytocin!\nYour signup code is %(otp)s.\nDon't share it with anyone."

otp_service = OTPService()


class SendSignUpOTPSerializer(serializers.Serializer):
    phone = serializers.CharField(
        min_length=10,
        max_length=10,
        source="user",
        write_only=True,
    )
    message = serializers.CharField(read_only=True)

    def validate_phone(self, value):
        if settings.DEBUG and not settings.TESTING:
            if value not in settings.SAFE_PHONE_NUMBERS:
                raise serializers.ValidationError(
                    _("This phone number is not allowed during development.")
                )
        if not value.startswith("09"):
            raise serializers.ValidationError(_("Phone number must start with '09'."))
        value = "+963" + value[1:]
        try:
            user = User.objects.not_deleted().get(phone=value)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                _("Please check the phone number and try again.")
            )
        if user.is_verified_phone:
            raise serializers.ValidationError(
                _("This phone number is already verified.")
            )
        return user

    def save(self, **kwargs):
        user = self.validated_data["user"]
        key = SIGNUP_KEY % {"user": user.id}
        otp = otp_service.generate(key)
        if not settings.TESTING:
            message = _(SIGNUP_MESSAGE) % {"otp": otp}
            send_sms.delay(user.phone, message)
        return {
            "message": _(
                "Your sign-in code has been sent. Please check your phone shortly."
            )
        }


class VerifySignUpOTPSerializer(serializers.Serializer):
    phone = serializers.CharField(
        min_length=10,
        max_length=10,
        source="user",
        write_only=True,
    )
    code = serializers.CharField(
        min_length=5,
        max_length=5,
        write_only=True,
    )
    access_token = serializers.CharField(read_only=True)
    refresh_token = serializers.CharField(read_only=True)
    expires_in = serializers.IntegerField(read_only=True)

    def validate_phone(self, value):
        if settings.DEBUG and not settings.TESTING:
            if value not in settings.SAFE_PHONE_NUMBERS:
                raise serializers.ValidationError(
                    _("This phone number is not allowed during development.")
                )
        if not value.startswith("09"):
            raise serializers.ValidationError(_("Phone number must start with '09'."))
        value = "+963" + value[1:]
        try:
            user = User.objects.not_deleted().get(phone=value)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                _("Please check the phone number and try again.")
            )
        if user.is_verified_phone:
            raise serializers.ValidationError(
                _("This phone number is already verified.")
            )
        return user

    def validate(self, data):
        user = data["user"]
        otp = data["code"]
        key = SIGNUP_KEY % {"user": user.id}
        otp_service.validate(key, otp)
        user.is_verified_phone = True
        user.save()
        refresh_token = RefreshToken.for_user(user)
        access_token = refresh_token.access_token
        expires_in = int(access_token.lifetime.total_seconds())
        return {
            "access_token": str(access_token),
            "refresh_token": str(refresh_token),
            "expires_in": expires_in,
        }
