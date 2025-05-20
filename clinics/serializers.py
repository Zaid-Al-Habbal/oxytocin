from django.utils.translation import gettext as _

from rest_framework import serializers

from users.models import CustomUser as User

from .models import Clinic


class ClinicSerializer(serializers.ModelSerializer):

    class Meta:
        model = Clinic
        fields = [
            "location",
            "longitude",
            "latitude",
            "phone",
        ]

    @property
    def user(self):
        return self.context["request"].user

    def validate(self, data):
        if self.user.role != User.Role.DOCTOR:
            raise serializers.ValidationError(_("You don't have the required role."))
        if not hasattr(self.user, "doctor"):
            raise serializers.ValidationError(
                _("Please create a doctor profile first.")
            )
        if self.instance is None and hasattr(self.user.doctor, "clinic"):
            raise serializers.ValidationError(_("You already have a clinic."))
        return super().validate(data)

    def create(self, validated_data):
        doctor = self.user.doctor
        return Clinic.objects.create(doctor=doctor, **validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
