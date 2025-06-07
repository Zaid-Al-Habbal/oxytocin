from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from rest_framework import serializers

from users.models import CustomUser as User


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
