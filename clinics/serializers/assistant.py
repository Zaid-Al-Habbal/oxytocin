from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from assistants.models import Assistant


class AddAssistantSerializer(serializers.Serializer):
    assistant_phone = serializers.CharField(write_only=True)

    def validate_assistant_phone(self, value):
        try:
            assistant = Assistant.objects.get(user__phone=value)
        except Assistant.DoesNotExist:
            raise serializers.ValidationError(
                _("There is no assistant with this phone number!")
            )

        if assistant.clinic is not None:
            raise serializers.ValidationError(
                _("This assistant is already connected to a clinic.")
            )

        self.context["assistant"] = assistant
        return value


class ListAssistantsSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True, source="user.id")
    full_name = serializers.CharField(read_only=True, source="user.full_name")
    phone = serializers.CharField(read_only=True, source="user.phone")
    image = serializers.ImageField(read_only=True, source="user.image")

    class Meta:
        model = Assistant
        fields = ["id", "full_name", "phone", "joined_clinic_at", "image"]
        read_only_fields = ["id", "joined_clinic_at"]
