from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from rest_framework import serializers
from file_validator.models import DjangoFileValidator
from rest_framework.exceptions import PermissionDenied

from .models import CustomUser as User


class UserCreateSerializer(serializers.ModelSerializer):

    ROLE_CHOICES = [
        ("doctor", "Doctor"),
        ("assistant", "Assistant"),
    ]

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
            "first_name",
            "last_name",
            "phone",
            "role",
            "password",
            "password_confirm",
        ]
        read_only_fields = ["image"]

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
