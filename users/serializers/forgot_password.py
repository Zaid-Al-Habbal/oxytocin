from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _
from django.conf import settings

from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import CustomUser as User
from users.services import OTPService
from users.tasks import send_sms


otp_service = OTPService()


class ForgetPasswordOTPSendSerializer(serializers.Serializer):
    phone = serializers.CharField(min_length=10, max_length=10)
    message = serializers.CharField(read_only=True)

    def save(self, **kwargs):
        phone = self.validated_data["phone"]
        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            raise serializers.ValidationError(_("Phone Number Not Found"))

        if not settings.TESTING:
            userKey = f"{user.id}:forget-password"
            otp = otp_service.generate(userKey)
            message = _("🩺 Oxytocin:\nUse code %(otp)s to reset your password.\nDon’t share this code with anyone.") % {"otp": otp}
            send_sms.delay(phone, message)


class ForgetPasswordOTPVerificationSerializer(serializers.Serializer):
    phone = serializers.CharField(min_length=10, max_length=10, write_only=True)

    verification_code = serializers.CharField(
        min_length=5,
        max_length=5,
        write_only=True,
    )
    access_token = serializers.CharField(read_only=True)
    refresh_token = serializers.CharField(read_only=True)
    expires_in = serializers.IntegerField(read_only=True)

    def validate(self, data):
        phone = data["phone"]
        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            raise serializers.ValidationError(_("Phone Number Not Found"))

        otp = data["verification_code"]

        userKey = f"{user.id}:forget-password"
        otp_service.verify_and_mark_as_verified(userKey, otp)

        if not user.is_verified_phone:
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


class AddNewPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
        style={"input_type": "password"},
        help_text="Password must meet the validation rules (min length=8, has both lowercase and uppercase latters, number, special character, not common, not similar to user's attributes ).",
    )

    def save(self, **kwargs):
        user = self.context["request"].user

        userKey = f"{user.id}:forget-password"
        otp_service.validate(userKey, "VERIFIED")

        user.set_password(self.validated_data["new_password"])
        user.save()
