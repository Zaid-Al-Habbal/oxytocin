from datetime import timedelta
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from django.contrib.gis.geos import Point
from appointments.models import Appointment
from archives.models import Archive, ArchiveAccessPermission
from clinics.models import Clinic
from common.utils import generate_test_pdf
from doctors.models import Doctor, DoctorSpecialty, Specialty
from users.models import CustomUser as User
from patients.models import Patient, PatientSpecialtyAccess

from .base import ArchiveBaseTestCase


class ArchiveRetrieveTestCase(ArchiveBaseTestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.path = reverse("archive-retrieve-update-destroy", kwargs={"pk": cls.archive.pk})
        cls.non_own_patient_user = User.objects.create_user(
            phone="0999111131",
            password="abcX123!",
            first_name="Souta",
            last_name="Munakata",
            role=User.Role.PATIENT.value,
            is_verified_phone=True,
            gender="male",
            birth_date="1995-05-01",
        )
        Patient.objects.create(
            user=cls.non_own_patient_user,
            address="Damascus",
            location=Point(36.29, 33.51, srid=4326),
            job="Engineer",
            blood_type="A+",
            medical_history="",
            surgical_history="",
            allergies="",
            medicines="",
            is_smoker=False,
            is_drinker=False,
            is_married=False,
        )
        cls.restricted_doctor_user = User.objects.create_user(
            phone="0999111124",
            password="abcX123!",
            first_name="Airi",
            last_name="Katagiri",
            role=User.Role.DOCTOR.value,
            is_verified_phone=True,
            gender="female",
            birth_date="1995-05-01",
        )
        doctor = Doctor.objects.create(
            user=cls.restricted_doctor_user,
            about="About Test",
            education="Test",
            certificate=generate_test_pdf(),
            start_work_date=timezone.now().date() - timedelta(days=30),
            status=Doctor.Status.APPROVED.value,
        )
        main_specialty2 = Specialty.objects.create(
            name_en="Test2",
            name_ar="تجريبي2",
        )
        DoctorSpecialty.objects.create(
            doctor=doctor,
            specialty=main_specialty2,
            university="Damascus",
        )
        clinic = Clinic.objects.create(
            doctor=doctor,
            address="Test Street",
            location=Point(44.2, 32.1, srid=4326),
            phone="011 223 3334",
        )
        appointment = Appointment.objects.create(
            patient=cls.patient_user,
            clinic=clinic,
            visit_date=timezone.now().date(),
            visit_time=timezone.now().time(),
            status=Appointment.Status.COMPLETED.value,
        )
        ArchiveAccessPermission.objects.create(
            patient=cls.patient,
            doctor=doctor,
            specialty=cls.main_specialty,
        )
        cls.public_archive = Archive.objects.create(
            patient=cls.patient,
            doctor=doctor,
            appointment=appointment,
            specialty=main_specialty2,
            main_complaint="string",
            case_history="string",
            cost=100.0,
        )
        cls.public_doctor_user = User.objects.create_user(
            phone="0999111125",
            password="abcX123!",
            first_name="Sachiko",
            last_name="Fujinuma",
            role=User.Role.DOCTOR.value,
            is_verified_phone=True,
            gender="female",
            birth_date="1995-05-01",
        )
        doctor = Doctor.objects.create(
            user=cls.public_doctor_user,
            about="About Test",
            education="Test",
            certificate=generate_test_pdf(),
            start_work_date=timezone.now().date() - timedelta(days=30),
            status=Doctor.Status.APPROVED.value,
        )
        main_specialty3 = Specialty.objects.create(
            name_en="Test3",
            name_ar="تجريبي3",
        )
        DoctorSpecialty.objects.create(
            doctor=doctor,
            specialty=main_specialty3,
            university="Damascus",
        )
        clinic = Clinic.objects.create(
            doctor=doctor,
            address="Test Street",
            location=Point(44.2, 32.1, srid=4326),
            phone="011 223 3335",
        )
        Appointment.objects.create(
            patient=cls.patient_user,
            clinic=clinic,
            visit_date=timezone.now().date(),
            visit_time=timezone.now().time(),
            status=Appointment.Status.COMPLETED.value,
        )
        PatientSpecialtyAccess.objects.create(
            patient=cls.patient,
            specialty=main_specialty2,
            visibility=PatientSpecialtyAccess.Visibility.PUBLIC.value,
        )

    def test_retrieve_successful_own_archive(self):
        self.client.force_authenticate(self.doctor_user)
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_successful_restricted_archive(self):
        self.client.force_authenticate(self.restricted_doctor_user)
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_successful_public_archive(self):
        path = reverse("archive-retrieve-update-destroy", kwargs={"pk": self.public_archive.pk})
        self.client.force_authenticate(self.public_doctor_user)
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_successful_patient_archive(self):
        self.client.force_authenticate(self.patient_user)
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_view_rejects_non_own_patient(self):
        self.client.force_authenticate(self.non_own_patient_user)
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_view_rejects_users_with_non_doctor_or_patient_role(self):
        self.client.force_authenticate(self.assistant_user)
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_view_rejects_unauthenticated_users(self):
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
