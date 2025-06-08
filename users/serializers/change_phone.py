from django.utils.translation import gettext_lazy as _
from django.core.cache import cache
from django.conf import settings

from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from users.models import CustomUser as User
from users.services import OTPService
from users.tasks import send_sms


CHANGE_PHONE_KEY = "change_phone:user:%(user)s"
NEW_PHONE_KEY = "new_phone:user:%(user)s"
CHANGE_PHONE_MESSAGE = "🩺 Oxytocin:\nUse code %(otp)s to confirm your phone number change.\nDon't share this code with anyone."

otp_service = OTPService()


class SendChangePhoneOTPSerializer(serializers.Serializer):
    phone = serializers.CharField(
        min_length=10,
        max_length=10,
        write_only=True,
        help_text=(
            "Must differ from the current user's phone number.\n"
            "Must be unique across all user records."
        ),
    )
    message = serializers.CharField(read_only=True)

    @property
    def request(self):
        return self.context.get("request")

    @property
    def user(self):
        return self.request.user

    def validate_phone(self, value):
        if settings.DEBUG and not settings.TESTING:
            if value not in settings.SAFE_PHONE_NUMBERS:
                raise serializers.ValidationError(
                    _("This phone number is not allowed during development.")
                )
        if not value.startswith("09"):
            raise serializers.ValidationError(_("Phone number must start with '09'."))
        if self.user.phone == value:
            raise serializers.ValidationError(
                _(
                    "The new phone number must be different from your current phone number."
                )
            )
        unique_validator = UniqueValidator(queryset=User.objects.all())
        unique_validator(value, self.fields["phone"])
        return value

    def save(self, **kwargs):
        phone = self.validated_data["phone"]
        key = CHANGE_PHONE_KEY % {"user": self.user.id}
        otp = otp_service.generate(key)
        key = NEW_PHONE_KEY % {"user": self.user.id}
        cache.set(key, phone, 360)  # Give phone number more timeout for safety
        if not settings.TESTING:
            message = _(CHANGE_PHONE_MESSAGE) % {"otp": otp}
            send_sms.delay(phone, message)
        return {
            "message": _(
                "Your change-phone code has been sent. Please check your phone shortly."
            )
        }


class VerifyChangePhoneOTPSerializer(serializers.Serializer):
    code = serializers.CharField(
        min_length=5,
        max_length=5,
        write_only=True,
    )
    message = serializers.CharField(read_only=True)
    phone = serializers.CharField(min_length=13, max_length=13, read_only=True)

    @property
    def request(self):
        return self.context.get("request")

    @property
    def user(self):
        return self.request.user

    def validate(self, data):
        otp = data["code"]
        key = CHANGE_PHONE_KEY % {"user": self.user.id}
        otp_service.validate(key, otp)
        key = NEW_PHONE_KEY % {"user": self.user.id}
        phone = cache.get(key)
        cache.delete(key)
        self.user.phone = phone
        self.user.save()
        return {
            "message": _("Phone number updated successfully."),
            "phone": phone,
        }
