from rest_framework.permissions import BasePermission

from archives.models import Archive
from archives.models import ArchiveAccessPermission

from patients.models import PatientSpecialtyAccess
from users.models import CustomUser as User

from appointments.models import Appointment


class ArchiveListPermission(BasePermission):
    def has_permission(self, request, view):
        patient_pk = view.kwargs.get("patient_pk")
        if not patient_pk:
            return False

        return Appointment.objects.filter(
            patient_id=patient_pk,
            clinic_id=request.user.pk,
        ).exists()


class ArchiveRetrievePermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        user: User = request.user
        archive: Archive = obj

        if user.role == User.Role.DOCTOR:
            specialty = archive.specialty
            patient = archive.patient
            return Appointment.objects.filter(
                patient_id=patient.pk,
                clinic_id=user.pk,
            ).exists() and (
                archive.doctor.pk == user.pk
                or ArchiveAccessPermission.objects.filter(
                    patient_id=patient.pk,
                    doctor_id=user.pk,
                    specialty_id=specialty.pk,
                ).exists()
                or PatientSpecialtyAccess.objects.public_only()
                .filter(patient_id=patient.pk)
                .exists()
            )
        else:
            return archive.patient.pk == user.pk


class ArchiveUpdatePermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        archive: Archive = obj
        appointment = archive.appointment
        if not appointment:
            return False
        doctor = archive.doctor
        return (
            appointment.status == Appointment.Status.IN_CONSULTATION
            and doctor.pk == request.user.pk
        )


class ArchiveDestroyPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        archive: Archive = obj
        patient = archive.patient
        return patient.pk == request.user.pk
