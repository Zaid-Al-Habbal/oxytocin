from django.utils.translation import gettext_lazy as _
from django.contrib.gis.geos import Point

from rest_framework import serializers

from users.serializers import (
    UserSerializer,
    UserNestedSerializer,
)
from users.models import CustomUser as User

from patients.models import Patient


class CompletePatientRegistrationSerializer(serializers.ModelSerializer):
    user = UserNestedSerializer()
    longitude = serializers.FloatField(min_value=-180.0, max_value=180.0)
    latitude = serializers.FloatField(min_value=-90.0, max_value=90.0)

    class Meta:
        model = Patient
        fields = [
            "user",
            "address",
            "longitude",
            "latitude",
            "job",
            "blood_type",
            "medical_history",
            "surgical_history",
            "allergies",
            "medicines",
            "is_smoker",
            "is_drinker",
            "is_married",
        ]

    def validate(self, data):
        user = self.context["request"].user
        if not user.is_verified_phone:
            raise serializers.ValidationError(_("Phone number is not verified."))
        if hasattr(user, "patient"):
            raise serializers.ValidationError(_("Patient profile already exists."))
        if user.role != User.Role.PATIENT:
            raise serializers.ValidationError(
                _("You have no access to complete this registration")
            )
        return data

    def create(self, validated_data):
        user = self.context["request"].user
        user_data = validated_data.pop("user")
        longitude = validated_data.pop("longitude")
        latitude = validated_data.pop("latitude")
        location = Point(longitude, latitude, srid=4326)

        user_serializer = UserNestedSerializer(user, data=user_data, partial=True)
        user_serializer.is_valid(raise_exception=True)
        user_serializer.save()

        return Patient.objects.create(user=user, location=location, **validated_data)


class PatientProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    longitude = serializers.FloatField(min_value=-180.0, max_value=180.0)
    latitude = serializers.FloatField(min_value=-90.0, max_value=90.0)

    class Meta:
        model = Patient
        fields = [
            "user",
            "address",
            "longitude",
            "latitude",
            "job",
            "blood_type",
            "medical_history",
            "surgical_history",
            "allergies",
            "medicines",
            "is_smoker",
            "is_drinker",
            "is_married",
        ]

    def update(self, instance, validated_data):
        user_data = validated_data.pop("user")
        longitude = validated_data.pop("longitude", "")
        latitude = validated_data.pop("latitude", "")
        if longitude and latitude:
            instance.location = Point(longitude, latitude, srid=4326)
        instance = super().update(instance, validated_data)

        user = instance.user
        user_serializer = UserSerializer(user, data=user_data, partial=True)
        user_serializer.is_valid(raise_exception=True)
        user_serializer.save()

        return instance


class LocationQuerySerializer(serializers.Serializer):
    longitude = serializers.FloatField(min_value=-180.0, max_value=180.0)
    latitude = serializers.FloatField(min_value=-90.0, max_value=90.0)
