from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from doctors.models import Specialty


class SpecialtySerializer(serializers.ModelSerializer):

    class Meta:
        model = Specialty
        fields = ["id", "name_en", "name_ar", "image"]


class SpecialtyListSerializer(serializers.ModelSerializer):
    subspecialties = SpecialtySerializer(many=True, read_only=True)

    class Meta:
        model = Specialty
        fields = ["id", "name_en", "name_ar", "image", "subspecialties"]
