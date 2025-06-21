from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from rest_framework import serializers

from users.models import CustomUser as User


class UserSerializer(serializers.ModelSerializer):

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

    def validate_birth_date(self, value):
        if value >= timezone.now().date():
            raise serializers.ValidationError(_("must be in the past."))
        return value

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
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


class UserSummarySerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = [
            "id",
            "first_name",
            "last_name",
            "image",
        ]


class UserDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ["id", "first_name", "last_name", "image", "gender", "age"]
