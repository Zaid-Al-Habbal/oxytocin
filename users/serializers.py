from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.conf import settings

from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from file_validator.models import DjangoFileValidator
from rest_framework.exceptions import PermissionDenied
from rest_framework_simplejwt.tokens import RefreshToken

from .models import CustomUser as User
from .services import OTPService
from .tasks import send_sms


otp_service = OTPService()


class UserCreateSerializer(serializers.ModelSerializer):

    ROLE_CHOICES = [
        ("doctor", "Doctor"),
        ("assistant", "Assistant"),
    ]

    phone = serializers.CharField(min_length=10, max_length=10)
    role = serializers.ChoiceField(choices=ROLE_CHOICES, default=User.Role.PATIENT)
    password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
        style={"input_type": "password"},
        help_text="Password must meet the validation rules (min length=8, has both lowercase and uppercase latters, number, special character, not common, not similar to user's attributes ).",
    )
    password_confirm = serializers.CharField(
        write_only=True, style={"input_type": "password"}
    )

    class Meta:
        model = User
        fields = [
            "id",
            "first_name",
            "last_name",
            "phone",
            "role",
            "password",
            "password_confirm",
        ]
        read_only_fields = ["image"]

    def validate_phone(self, value):
        if settings.TESTING:
            return value
        if settings.DEBUG:
            if value not in settings.SAFE_PHONE_NUMBERS:
                raise serializers.ValidationError(
                    _("This phone number is not allowed during development.")
                )
        if not value.startswith("09"):
            raise serializers.ValidationError(_("Phone number must start with '09'."))
        value = "+963" + value[1:]
        unique_validator = UniqueValidator(queryset=User.objects.all())
        unique_validator(value, self.fields["phone"])
        return value

    def validate(self, data):
        if data["password"] != data["password_confirm"]:
            raise serializers.ValidationError(
                {"password_confirm": _("Passwords don't match!")}
            )
        return data

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "phone",
            "image",
            "gender",
            "birth_date",
        ]
        read_only_fields = ["phone", "image"]

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

            # if this serializer was instantiated as `partial=True`,
            # make all fields optional
            if getattr(self, "partial", False):
                for field in self.fields.values():
                    field.required = False

    def update(self, instance, validated_data):
        instance.first_name = validated_data.get("first_name", instance.first_name)
        instance.last_name = validated_data.get("last_name", instance.last_name)
        instance.image = validated_data.get("image", instance.image)
        instance.gender = validated_data.get("gender", instance.gender)
        instance.birth_date = validated_data.get("birth_date", instance.birth_date)
        instance.save()
        return instance


class UserNestedSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ["gender", "birth_date"]
        extra_kwargs = {
            "gender": {"required": True},
            "birth_date": {"required": True},
        }

    def validate_birth_date(self, value):
        if value >= timezone.now().date():
            raise serializers.ValidationError(_("must be in the past."))
        return value


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
    )
    new_password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
        style={"input_type": "password"},
        help_text="Password must meet the validation rules (min length=8, has both lowercase and uppercase latters, number, special character, not common, not similar to user's attributes ).",
    )
    new_password_confirm = serializers.CharField(
        write_only=True, style={"input_type": "password"}
    )

    def validate(self, data):
        if data["new_password"] != data["new_password_confirm"]:
            raise serializers.ValidationError(
                {"password_confirm": _("Passwords don't match!")}
            )
        return data

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError(_("Old password is not correct."))
        return value

    def save(self, **kwargs):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save()
        return user


class UserImageSerializer(serializers.Serializer):
    image = serializers.ImageField(
        validators=[
            DjangoFileValidator(
                libraries=["python_magic", "filetype"],
                acceptable_mimes=[
                    "image/jpg",
                    "image/jpeg",
                    "image/png",
                    "image/gif",
                    "image/webp",
                    "image/bmp",
                ],
                acceptable_types=["image"],
                max_upload_file_size=5 * 1024 * 1024,  # 5MB
            )
        ],
        help_text="Accepted MIME types: image/jpg, image/jpeg, image/png, image/gif, image/webp, image/bmp. Max file size: 5MB.",
    )

    @property
    def request(self):
        return self.context.get("request")

    @property
    def user(self):
        return self.request.user

    def validate(self, data):
        if not self.user.is_verified_phone:
            raise PermissionDenied(_("Phone number is not verified."))
        return data

    def create(self, validated_data):
        self.user.image = validated_data["image"]
        self.user.save()
        return self.user


class UserPhoneVerificationSendSerializer(serializers.Serializer):
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.not_deleted().all(),
        source="user",
        write_only=True,
    )
    message = serializers.CharField(read_only=True)

    def save(self, **kwargs):
        user = self.validated_data["user"]
        if not settings.TESTING:
            otp = otp_service.generate(user.id)
            message = _(settings.VERIFICATION_CODE_MESSAGE  % {"otp": otp})
            send_sms.delay(user.id, message)


class UserPhoneVerificationSerializer(serializers.Serializer):
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.not_deleted().not_verified_phone().all(),
        source="user",
        write_only=True,
    )
    verification_code = serializers.CharField(
        min_length=5,
        max_length=5,
        write_only=True,
    )
    access_token = serializers.CharField(read_only=True)
    refresh_token = serializers.CharField(read_only=True)
    expires_in = serializers.IntegerField(read_only=True)

    def validate(self, data):
        user = data["user"]
        otp = data["verification_code"]
        otp_service.validate(user.id, otp)
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
            message = _(settings.FORGET_PASSWORD_CODE  % {"otp": otp})
            send_sms.delay(user.id, message)
            

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
        otp_service.validate(userKey, otp)
        
        if not user.is_verified_phone:
            user.is_verified_phone = True
            user.save()
        
        if not settings.TESTING:
            userKey = f"{user.id}:forget-password:verfied"
            otp = otp_service.generate(userKey)
        
        refresh_token = RefreshToken.for_user(user)
        access_token = refresh_token.access_token
        expires_in = int(access_token.lifetime.total_seconds())
        
        return {
            "access_token": str(access_token),
            "refresh_token": str(refresh_token),
            "expires_in": expires_in,
        }
