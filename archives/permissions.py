from rest_framework.permissions import BasePermission
from rest_framework.exceptions import ValidationError

from archives.models import Archive
from archives.models import ArchiveAccessPermission

from doctors.models import Doctor, Specialty

from patients.models import Patient, PatientSpecialtyAccess

from users.models import CustomUser as User

from appointments.models import Appointment


class ArchiveListPermission(BasePermission):
    def has_permission(self, request, view):
        patient_id = request.query_params.get("patient_id")
        if not patient_id:
            raise ValidationError({"patient_id": "This field is required."})

        user: User = request.user
        return Appointment.objects.filter(
            patient_id=patient_id,
            clinic_id=user.pk,
        ).exists()


class ArchiveRetrievePermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        user: User = request.user
        archive: Archive = obj

        if user.role == User.Role.DOCTOR:
            doctor: Doctor = user.doctor
            specialty: Specialty = archive.specialty
            patient: Patient = archive.patient
            # has previous appointment with this doctor
            return Appointment.objects.filter(
                patient_id=patient.pk,
                clinic_id=user.pk,
            ).exists() and (
                # belongs to this doctor
                archive.doctor.pk == doctor.pk
                # or same specialty as doctor
                or specialty.pk == doctor.main_specialty.specialty.pk
                # or has access permission
                or ArchiveAccessPermission.objects.filter(
                    patient_id=patient.pk,
                    doctor_id=user.pk,
                    specialty_id=specialty.pk,
                ).exists()
                # or public access
                or PatientSpecialtyAccess.objects.public_only()
                .filter(
                    patient_id=patient.pk,
                    specialty_id=specialty.pk,
                )
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
        user: User = request.user
        return (
            appointment.status == Appointment.Status.IN_CONSULTATION
            and doctor.pk == user.pk
        )


class ArchiveDestroyPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        archive: Archive = obj
        patient = archive.patient
        user: User = request.user
        return patient.pk == user.pk
