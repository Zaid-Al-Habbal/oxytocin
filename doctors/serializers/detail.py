from rest_framework import serializers

from doctors.models import Doctor, Specialty, DoctorSpecialty
from users.serializers import UserDetailSerializer
from clinics.serializers import ClinicSerializer

from .specialty import SpecialtySerializer


class DoctorSpecialtyDetailSerializer(serializers.ModelSerializer):
    specialty_id = serializers.PrimaryKeyRelatedField(
        queryset=Specialty.objects.with_main_specialties().all(),
        source="specialty",
        write_only=True,
    )
    specialty = SpecialtySerializer(read_only=True)

    class Meta:
        model = DoctorSpecialty
        fields = ["specialty_id", "specialty", "university"]


class DoctorDetailSerializer(serializers.ModelSerializer):
    user = UserDetailSerializer()
    experience = serializers.IntegerField(read_only=True)
    rate = serializers.FloatField(read_only=True)
    main_specialty = DoctorSpecialtyDetailSerializer()
    subspecialties = DoctorSpecialtyDetailSerializer(many=True)
    clinic = ClinicSerializer()
    is_favorite = serializers.BooleanField(read_only=True)

    class Meta:
        model = Doctor
        fields = [
            "user",
            "about",
            "education",
            "experience",
            "rate",
            "main_specialty",
            "subspecialties",
            "clinic",
            "is_favorite",
        ]
        read_only_fields = ["rate"]
