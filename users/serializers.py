from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers


User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, style={"input_type": "password"})
    password_confirm = serializers.CharField(
        write_only=True, style={"input_type": "password"}
    )

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "phone",
            "email",
            "image",
            "gender",
            "birth_date",
            "password",
            "password_confirm",
        ]

    def validate_email(self, value):
        if not value:
            return None
        return value

    def validate_password(self, value):
        validate_password(value)
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

    def update(self, instance, validated_data):
        instance.first_name = validated_data.get("first_name", instance.first_name)
        instance.last_name = validated_data.get("last_name", instance.last_name)
        instance.image = validated_data.get("image", instance.image)
        instance.gender = validated_data.get("gender", instance.gender)
        instance.birth_date = validated_data.get("birth_date", instance.birth_date)
        instance.save()
        return instance
