from rest_framework import serializers

from users.models import CustomUser as User
from doctors.models import Doctor, Specialty
from .base import DoctorSummarySerializer, SpecialtySerializer


class DoctorFilterQuerySerializer(serializers.Serializer):
    DISTANCE_UNIT_CHOICES = [
        ("m", "Meters"),
        ("km", "Kilometers"),
        ("mi", "Miles"),
        ("ft", "Feet"),
    ]

    specialties = serializers.CharField(required=False)
    gender = serializers.ChoiceField(choices=User.Gender.choices, required=False)
    distance = serializers.FloatField(required=False)
    unit = serializers.ChoiceField(choices=DISTANCE_UNIT_CHOICES, required=False)

    def validate_specialties(self, value):
        specialties_list = [v.strip() for v in value.split(",") if v.strip()]
        specialties = Specialty.objects.filter(pk__in=specialties_list)
        return specialties


class DoctorMultiSearchResultSerializer(serializers.Serializer):
    doctors = DoctorSummarySerializer(many=True, read_only=True)
    specialties = SpecialtySerializer(many=True, read_only=True)
