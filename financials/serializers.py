from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from financials.models import Financial, Payment
from clinics.serializers.summary import ClinicSummarySerializer
from patients.serializers.summary import PatientSummarySerializer


class FinancialPatientSerializer(serializers.ModelSerializer):
    clinic = ClinicSummarySerializer(read_only=True)

    class Meta:
        model = Financial
        fields = ["id", "clinic", "cost", "created_at", "updated_at"]
        read_only_fields = ["id", "cost", "created_at", "updated_at"]


class FinancialClinicSerializer(serializers.ModelSerializer):
    patient = PatientSummarySerializer(read_only=True)

    class Meta:
        model = Financial
        fields = ["id", "patient", "cost", "created_at", "updated_at"]
        read_only_fields = ["id", "cost", "created_at", "updated_at"]

    def validate_cost(self, value):
        if value <= 0:
            raise serializers.ValidationError(_("must be greater than 0"))
        if value > self.instance.cost:
            raise serializers.ValidationError(_("must be less than or equal to the cost"))
        return value

    def update(self, instance, validated_data):
        cost = validated_data.pop("cost")
        instance.cost -= cost
        Payment.objects.create(
            clinic=instance.clinic,
            patient=instance.patient,
            cost=cost,
        )
        instance.save()
        return instance
