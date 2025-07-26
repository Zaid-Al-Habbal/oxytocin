from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from doctors.models import Doctor
from doctors.serializers.summary import DoctorSummarySerializer
from favorites.models import Favorite
from patients.serializers.summary import PatientSummarySerializer


class FavoriteSerializer(serializers.ModelSerializer):
    patient = PatientSummarySerializer(read_only=True)
    doctor_id = serializers.PrimaryKeyRelatedField(
        queryset=Doctor.objects.not_deleted(),
        source="doctor",
        write_only=True,
    )
    doctor = DoctorSummarySerializer(read_only=True)

    class Meta:
        model = Favorite
        fields = ["id", "patient", "doctor_id", "doctor", "created_at"]
        read_only_fields = ["id", "created_at"]

    @property
    def request(self):
        return self.context.get("request")

    @property
    def user(self):
        return self.request.user

    def validate_doctor_id(self, value):
        doctor: Doctor = value
        if Favorite.objects.filter(
            patient_id=self.user.pk,
            doctor_id=doctor.pk,
        ).exists():
            msg = _('Invalid pk "%(value)s" - doctor already in favorite.')
            raise serializers.ValidationError(msg % {"value": doctor.pk})
        return value
