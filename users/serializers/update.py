from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from users.models import CustomUser as User


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
