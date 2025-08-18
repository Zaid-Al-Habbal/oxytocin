from django.utils.translation import gettext_lazy as _
from django.db import transaction
from django.db.models import F

from rest_framework import serializers

from financials.models import Financial, Payment
from clinics.serializers.summary import ClinicSummarySerializer
from patients.serializers.summary import PatientSummarySerializer
from archives.models import Archive


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
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_cost(self, value):
        if value <= 0:
            raise serializers.ValidationError(_("must be greater than 0"))
        if value > self.instance.cost:
            raise serializers.ValidationError(
                _("must be less than or equal to the cost")
            )
        return value

    @transaction.atomic
    def update(self, instance, validated_data):
        cost = validated_data.pop("cost")
        instance.cost -= cost
        instance.save()
        Payment.objects.create(
            clinic=instance.clinic,
            patient=instance.patient,
            cost=cost,
        )
        remaining = cost
        archives = list(
            Archive.objects.filter(
                patient_id=instance.patient_id,
                doctor_id=instance.clinic_id,
                paid__lt=F("cost"),
            )
            .order_by("created_at")
            .select_for_update()
        )

        archives_to_update = []
        for archive in archives:
            if remaining <= 0:
                break
            outstanding = archive.cost - archive.paid
            applied = outstanding if outstanding <= remaining else remaining
            archive.paid = archive.paid + applied
            remaining -= applied
            archives_to_update.append(archive)

        if archives_to_update:
            Archive.objects.bulk_update(archives_to_update, ["paid"])
        return instance
