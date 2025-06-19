from rest_framework import serializers

from users.models import CustomUser as User
from doctors.models import Specialty


class ClinicFilterQuerySerializer(serializers.Serializer):
    DISTANCE_UNIT_CHOICES = [
        ("m", "Meters"),
        ("km", "Kilometers"),
        ("mi", "Miles"),
        ("ft", "Feet"),
    ]

    specialties = serializers.CharField(required=False)
    gender = serializers.ChoiceField(choices=User.Gender.choices, required=False)
    distance = serializers.IntegerField(required=False)
    unit = serializers.ChoiceField(choices=DISTANCE_UNIT_CHOICES, required=False)

    def validate_specialties(self, value):
        specialties_list = [v.strip() for v in value.split(",") if v.strip()]
        valid_specialties = set(Specialty.objects.values_list("name_en", flat=True))
        return [
            specialty
            for specialty in specialties_list
            if specialty in valid_specialties
        ]


class ClinicOrderByQuerySerializer(serializers.Serializer):
    ORDER_BY_MAP = {
        "experience": "start_work_date",
        "rate": "rate",
        "distance": "distance",
    }

    order_by = serializers.CharField(required=False)

    def validate_order_by(self, value):
        order_by_list = [v.strip() for v in value.split(",") if v.strip()]
        filtered_order_by = []
        for item in order_by_list:
            direction = "-" if item.startswith("-") else ""
            key = item.lstrip("-")
            if key in self.ORDER_BY_MAP.keys():
                mapped_key = self.ORDER_BY_MAP[key]
                filtered_order_by.append((direction, mapped_key))
        return filtered_order_by
