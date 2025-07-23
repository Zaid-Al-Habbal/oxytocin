from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from doctors.models import Specialty
from doctors.serializers import SpecialtySerializer

from patients.models import Patient, PatientSpecialtyAccess


class PatientSpecialtyAccessListCreateSerializer(serializers.ModelSerializer):
    specialty_id = serializers.PrimaryKeyRelatedField(
        queryset=Specialty.objects.main_specialties_only().all(),
        source="specialty",
        write_only=True,
    )
    specialty = SpecialtySerializer(read_only=True)

    class Meta:
        model = PatientSpecialtyAccess
        fields = [
            "id",
            "specialty_id",
            "specialty",
            "visibility",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    @property
    def request(self):
        return self.context.get("request")

    @property
    def user(self):
        return self.request.user

    def validate_specialty_id(self, value):
        patient: Patient = self.user.patient
        specialty: Specialty = value
        exists = PatientSpecialtyAccess.objects.filter(
            patient__pk=patient.pk,
            specialty__pk=specialty.pk,
        ).exists()
        if exists:
            msg = _('Invalid pk "%(value)s" - object already attached with patient.')
            raise serializers.ValidationError(msg % {"value": specialty.pk})
        return value


class PatientSpecialtyAccessSerializer(serializers.ModelSerializer):
    specialty = SpecialtySerializer(read_only=True)

    class Meta:
        model = PatientSpecialtyAccess
        fields = [
            "id",
            "specialty",
            "visibility",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
