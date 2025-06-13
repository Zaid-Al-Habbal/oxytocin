from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from doctors.models import Specialty, DoctorSpecialty

from .specialty_serializer import SpecialtySerializer


class DoctorSpecialtySerializer(serializers.ModelSerializer):
    specialty_id = serializers.PrimaryKeyRelatedField(
        queryset=Specialty.objects.with_main_specialties().all(),
        source="specialty",
        write_only=True,
    )
    specialty = SpecialtySerializer(read_only=True)

    class Meta:
        model = DoctorSpecialty
        fields = ["specialty_id", "specialty", "university", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]
