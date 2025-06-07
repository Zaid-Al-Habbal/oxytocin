from django.utils.translation import gettext_lazy as _

from file_validator.models import DjangoFileValidator
from rest_framework.exceptions import PermissionDenied
from rest_framework import serializers


class ImageSerializer(serializers.Serializer):
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
