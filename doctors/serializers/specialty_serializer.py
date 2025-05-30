from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from doctors.models import Specialty


class SpecialtySerializer(serializers.ModelSerializer):

    class Meta:
        model = Specialty
        fields = ["id", "name_en", "name_ar"]
