from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from file_validator.models import DjangoFileValidator

from clinics.models import ClinicImage
from clinics.serializers import ClinicMixin


class NestedClinicImageSerializer(ClinicMixin, serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=ClinicImage.objects.none(),  # override in the get_fields
    )
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

    class Meta:
        model = ClinicImage
        fields = ["id", "image", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]

    def get_fields(self):
        fields = super().get_fields()
        if hasattr(self.user, "doctor") and hasattr(self.user.doctor, "clinic"):
            clinic = self.user.doctor.clinic
            fields["id"].queryset = ClinicImage.objects.filter(clinic=clinic)
        return fields

    def validate(self, data):
        if "id" not in data:
            raise serializers.ValidationError({"id": _("This field is required.")})
        if "image" not in data:
            raise serializers.ValidationError({"image": _("This field is required.")})
        return super().validate(data)


class ClinicImageSerializer(ClinicMixin, serializers.ModelSerializer):
    class Meta:
        model = ClinicImage
        fields = ["id", "image", "created_at", "updated_at"]
        read_only_fields = ["id", "image", "created_at", "updated_at"]


class ClinicImageCreateSerializer(ClinicMixin, serializers.Serializer):
    images = serializers.ListField(
        child=serializers.ImageField(
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
        ),
        max_length=8,
        help_text="Accepted MIME types: image/jpg, image/jpeg, image/png, image/gif, image/webp, image/bmp. Max file size: 5MB.",
    )

    def validate_images(self, value):
        uploaded_images_len = len(value)
        clinic = self.user.doctor.clinic
        existing_image_count = clinic.images.count()
        total_images = existing_image_count + uploaded_images_len
        if total_images > 8:
            raise serializers.ValidationError(
                _("You can upload a maximum of 8 images.")
            )
        return value

    def to_representation(self, instance):
        serializer = NestedClinicImageSerializer(
            instance,
            many=True,
            context=self.context,
        )
        return {"clinic_images": serializer.data}

    def create(self, validated_data):
        images = validated_data.pop("images")

        clinic = self.user.doctor.clinic
        saved_clinic_images = ClinicImage.objects.bulk_create(
            [ClinicImage(clinic=clinic, image=image) for image in images]
        )
        return saved_clinic_images


class ClinicImagesUpdateSerializer(ClinicMixin, serializers.Serializer):
    clinic_images = NestedClinicImageSerializer(many=True)

    def to_representation(self, instance):
        serializer = NestedClinicImageSerializer(
            instance,
            many=True,
            context=self.context,
        )
        return {"clinic_images": serializer.data}

    def update(self, instance, validated_data):
        clinic_images = validated_data.pop("clinic_images")

        updated_clinic_images = []
        for obj in clinic_images:
            clinic_image = obj["id"]
            new_image = obj["image"]
            clinic_image.image = new_image
            clinic_image.save()
            updated_clinic_images.append(clinic_image)
        return updated_clinic_images


class ClinicImageDeleteSerializer(ClinicMixin, serializers.Serializer):
    clinic_images = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(queryset=ClinicImage.objects.all()),
        max_length=8,
    )

    def validate_clinic_images(self, value):
        clinic = self.user.doctor.clinic
        if len(value) != len(set(value)):
            raise serializers.ValidationError(_("Duplicate is not allowed."))
        for clinic_image in value:
            if clinic_image.clinic != clinic:
                msg = _('Invalid pk "%(value)s" - object does not exist.')
                raise serializers.ValidationError(_(msg % {"value": clinic_image.id}))
        return value
