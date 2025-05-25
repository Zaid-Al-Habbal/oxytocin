from django.utils.translation import gettext as _
from django.contrib.auth import authenticate

from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from rest_framework_simplejwt.tokens import RefreshToken
from file_validator.models import DjangoFileValidator

from users.models import CustomUser as User
from users.serializers import UserUpdateDestroySerializer, UserNestedSerializer

from .models import Doctor, Specialty


class DoctorLoginSerializer(serializers.Serializer):
    phone = serializers.CharField()
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate(self, data):
        phone = data.get("phone")
        password = data.get("password")
        user = authenticate(phone=phone, password=password)
        if (
            user is None
            or user.role != User.Role.DOCTOR.value
            or user.deleted_at is not None
        ):
            raise serializers.ValidationError(_("Invalid credentials!"))
        if not user.is_verified_phone:
            raise serializers.ValidationError(
                _("Please, verify your phone number first")
            )
        refresh_token = RefreshToken.for_user(user)
        access_token = refresh_token.access_token
        expires_in = int(access_token.lifetime.total_seconds())
        return {
            "access_token": str(access_token),
            "refresh_token": str(refresh_token),
            "expires_in": expires_in,
        }


class DoctorCreateSerializer(serializers.ModelSerializer):
    user = UserNestedSerializer()
    certificate = serializers.FileField(
        validators=[
            DjangoFileValidator(
                libraries=["python_magic", "filetype"],
                acceptable_mimes=[
                    "application/pdf",
                    "image/jpg",
                    "image/jpeg",
                    "image/png",
                    "image/gif",
                    "image/webp",
                    "image/bmp",
                ],
                acceptable_types=["archive", "image"],
                max_upload_file_size=8 * 1024 * 1024,  # 8MB
            )
        ],
        write_only=True,
    )
    specialties = serializers.SlugRelatedField(
        slug_field="name",
        queryset=Specialty.objects.all(),
        many=True,
    )

    class Meta:
        model = Doctor
        fields = [
            "user",
            "about",
            "education",
            "start_work_date",
            "certificate",
            "status",
            "specialties",
        ]
        read_only_fields = ["status"]

    def validate(self, data):
        user = self.context["request"].user
        if not user.is_verified_phone:
            raise serializers.ValidationError(_("Phone number is not verified."))
        if user.role != User.Role.DOCTOR.value:
            raise PermissionDenied(_("You don't have the required role."))
        if hasattr(user, "doctor"):
            raise serializers.ValidationError(_("You already have a doctor profile."))
        return super().validate(data)

    def create(self, validated_data):
        user_data = validated_data.pop("user")
        specialties = validated_data.pop("specialties")

        user = self.context["request"].user
        user_serializer = UserNestedSerializer(
            instance=user,
            data=user_data,
            partial=True,
        )
        user_serializer.is_valid(raise_exception=True)
        user = user_serializer.save()

        doctor = Doctor.objects.create(user=user, **validated_data)
        doctor.specialties.set(specialties)

        return doctor


class DoctorUpdateSerializer(serializers.ModelSerializer):
    user = UserUpdateDestroySerializer()
    specialties = serializers.SlugRelatedField(
        many=True,
        slug_field="name",
        queryset=Specialty.objects.all(),
    )

    class Meta:
        model = Doctor
        fields = [
            "user",
            "about",
            "education",
            "start_work_date",
            "status",
            "specialties",
        ]
        read_only_fields = ["status"]

    def update(self, instance, validated_data):
        user_data = validated_data.pop("user")
        specialties_data = validated_data.pop("specialties")

        user = instance.user
        user_serializer = UserUpdateDestroySerializer(
            instance=user,
            data=user_data,
            partial=True,
        )
        user_serializer.is_valid(raise_exception=True)
        user_serializer.save()

        instance.about = validated_data.get("about")
        instance.education = validated_data.get("education")
        instance.start_work_date = validated_data.get("start_work_date")
        instance.save()

        instance.specialties.set(specialties_data)

        return instance
