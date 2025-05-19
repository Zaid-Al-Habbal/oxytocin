from django.utils.translation import gettext as _
from django.contrib.auth import authenticate

from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import CustomUser as User
from users.serializers import UserUpdateDestroySerializer, UserNestedSerializer
from .models import Doctor, Specialty, Clinic


class ClinicSerializer(serializers.ModelSerializer):

    class Meta:
        model = Clinic
        fields = [
            "location",
            "longitude",
            "latitude",
            "phone",
        ]
        extra_kwargs = {
            # Remove DRF's automatic UniqueValidator on `phone`
            "phone": {"validators": []}
        }

    def validate_phone(self, value):
        queryset = Clinic.objects.all()
        validator = UniqueValidator(queryset=queryset)
        serializer_field = self.fields["phone"]
        validator(value, serializer_field)
        return value

    def create(self, validated_data):
        doctor = self.context.get("doctor")
        return Clinic.objects.create(doctor=doctor, **validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


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
    specialties = serializers.SlugRelatedField(
        slug_field="name",
        queryset=Specialty.objects.all(),
        many=True,
    )
    clinic = ClinicSerializer()

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
            "clinic",
        ]
        read_only_fields = ["status"]

    def validate(self, data):
        user = self.context["request"].user
        if not user.is_verified_phone:
            raise serializers.ValidationError(_("Phone number is not verified."))
        if user.role != User.Role.DOCTOR.value:
            raise serializers.ValidationError(_("You don't have the required rule."))
        if hasattr(user, "doctor"):
            raise serializers.ValidationError(_("You already have a doctor profile."))
        return super().validate(data)

    def create(self, validated_data):
        user_data = validated_data.pop("user")
        clinic_data = validated_data.pop("clinic")
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

        clinic_serializer = ClinicSerializer(
            data=clinic_data, context={"doctor": doctor}
        )
        clinic_serializer.is_valid(raise_exception=True)
        clinic_serializer.save()

        return doctor


class DoctorUpdateSerializer(serializers.ModelSerializer):
    user = UserUpdateDestroySerializer()
    specialties = serializers.SlugRelatedField(
        many=True,
        slug_field="name",
        queryset=Specialty.objects.all(),
    )
    clinic = ClinicSerializer()

    class Meta:
        model = Doctor
        fields = [
            "user",
            "about",
            "education",
            "start_work_date",
            "status",
            "specialties",
            "clinic",
        ]
        read_only_fields = ["status"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and hasattr(self.instance, "clinic"):
            self.fields["clinic"].instance = self.instance.clinic

    def update(self, instance, validated_data):
        user_data = validated_data.pop("user")
        specialties_data = validated_data.pop("specialties")
        clinic_data = validated_data.pop("clinic")

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

        clinic = instance.clinic
        clinic_serializer = ClinicSerializer(
            instance=clinic,
            data=clinic_data,
            partial=True,
        )
        clinic_serializer.is_valid(raise_exception=True)
        clinic_serializer.save()

        return instance
