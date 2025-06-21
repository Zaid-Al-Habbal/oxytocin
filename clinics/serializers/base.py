from django.contrib.gis.geos import Point
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from doctors.serializers import DoctorSummarySerializer

from users.models import CustomUser as User
from clinics.models import Clinic


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
    longitude = serializers.FloatField(min_value=-180.0, max_value=180.0)
    latitude = serializers.FloatField(min_value=-90.0, max_value=90.0)

    class Meta:
        model = Clinic
        fields = [
            "address",
            "longitude",
            "latitude",
            "phone",
        ]

    def validate(self, data):
        if self.user.role != User.Role.DOCTOR:
            raise PermissionDenied(_("You don't have the required role."))
        if not hasattr(self.user, "doctor"):
            raise PermissionDenied(_("Please create a doctor profile first."))
        certificate = self.user.doctor.certificate
        if not certificate:
            raise PermissionDenied(_("Please upload a certificate first."))
        if self.request.method == "POST" and hasattr(self.user.doctor, "clinic"):
            raise serializers.ValidationError(_("You already have a clinic."))
        return super().validate(data)

    def create(self, validated_data):
        doctor = self.user.doctor
        longitude = validated_data.pop("longitude")
        latitude = validated_data.pop("latitude")
        location = Point(longitude, latitude, srid=4326)
        return Clinic.objects.create(doctor=doctor, location=location, **validated_data)

    def update(self, instance, validated_data):
        longitude = validated_data.pop("longitude", "")
        latitude = validated_data.pop("latitude", "")
        if longitude and latitude:
            instance.location = Point(longitude, latitude, srid=4326)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class ClinicNearestSerializer(serializers.ModelSerializer):
    doctor = DoctorSummarySerializer()
    distance = serializers.IntegerField()

    class Meta:
        model = Clinic
        fields = ["doctor", "address", "distance"]
