from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _
from django.conf import settings

from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from users.models import CustomUser as User


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
