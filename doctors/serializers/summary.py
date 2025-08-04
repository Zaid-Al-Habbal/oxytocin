from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field

from doctors.models import Doctor
from users.serializers import UserSummarySerializer

from .specialty import SpecialtySerializer


class DoctorSummarySerializer(serializers.ModelSerializer):
    user = UserSummarySerializer()
    main_specialty = serializers.SerializerMethodField()

    class Meta:
        model = Doctor
        fields = [
            "user",
            "about",
            "main_specialty",
            "rate",
        ]
        read_only_fields = ["rate"]

    @extend_schema_field(SpecialtySerializer)
    def get_main_specialty(self, obj):
        main_specialty = obj.specialties.main_specialties_only()[0]
        serializer = SpecialtySerializer(main_specialty)
        return serializer.data
