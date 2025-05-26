from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from file_validator.models import DjangoFileValidator

from users.models import CustomUser as User

from .models import Clinic, ClinicImage


class ClinicMixin:
    """
    Mixin providing convenient access to the current request and user objects
    from the serializer context.
    """

    @property
    def request(self):
        return self.context.get("request")

    @property
    def user(self):
        return self.request.user


class ClinicSerializer(ClinicMixin, serializers.ModelSerializer):

    class Meta:
        model = Clinic
        fields = [
            "location",
            "longitude",
            "latitude",
            "phone",
        ]

    def validate(self, data):
        if self.user.role != User.Role.DOCTOR:
            raise PermissionDenied(_("You don't have the required role."))
        if not hasattr(self.user, "doctor"):
            raise serializers.ValidationError(
                _("Please create a doctor profile first.")
            )
        if self.request.method == "POST" and hasattr(self.user.doctor, "clinic"):
            raise serializers.ValidationError(_("You already have a clinic."))
        return super().validate(data)

    def create(self, validated_data):
        doctor = self.user.doctor
        return Clinic.objects.create(doctor=doctor, **validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


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
    )

    def validate_images(self, value):
        uploaded_images_len = len(value)
        if hasattr(self.user, "doctor") and hasattr(self.user.doctor, "clinic"):
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
    clinic_images = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=ClinicImage.objects.all(),
    )

    def validate_clinic_images(self, value):
        if hasattr(self.user, "doctor") and hasattr(self.user.doctor, "clinic"):
            clinic = self.user.doctor.clinic
            for clinic_image in value:
                if clinic_image.clinic != clinic:
                    msg = _('Invalid pk "%(value)s" - object does not exist.')
                    raise serializers.ValidationError(
                        _(msg % {"value": clinic_image.id})
                    )

            clinic_images_len = len(value)
            existing_clinic_image_count = clinic.images.count()
            if clinic_images_len > existing_clinic_image_count:
                raise serializers.ValidationError(
                    _(
                        "You cannot delete more images than currently exist for this clinic."
                    )
                )
        return value
