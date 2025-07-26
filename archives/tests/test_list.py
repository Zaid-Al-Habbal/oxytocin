from datetime import timedelta
from django.utils import timezone
from django.contrib.gis.geos import Point
from django.urls import reverse
from appointments.models import Appointment
from clinics.models import Clinic
from common.utils import generate_test_pdf
from doctors.models import Doctor, DoctorSpecialty
from users.models import CustomUser as User
from patients.models import Patient
from rest_framework import status

from .base import ArchiveBaseTestCase


class ArchiveListTestCase(ArchiveBaseTestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.path = reverse("archive-list", kwargs={"patient_pk": cls.patient_user.pk})
        patient_user = User.objects.create_user(
            phone="0999111124",
            password="abcX123!",
            first_name="Gaku",
            last_name="Yashiro",
            role=User.Role.PATIENT.value,
            is_verified_phone=True,
            gender="male",
            birth_date="1995-05-01",
        )
        Patient.objects.create(
            user=patient_user,
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
        cls.waiting_appointment = Appointment.objects.create(
            patient=patient_user,
            clinic=cls.clinic,
            visit_date=timezone.now().date() + timedelta(days=30),
            visit_time=timezone.now().time(),
            status=Appointment.Status.IN_CONSULTATION.value,
        )

    def test_list_successful(self):
        self.client.force_authenticate(self.doctor_user)
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertIn("results", str(data))

    def test_view_rejects_doctors_has_no_appointments_for_patient(self):
        doctor_user = User.objects.create_user(
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
            user=doctor_user,
            about="About Test",
            education="Test",
            certificate=generate_test_pdf(),
            start_work_date=timezone.now().date() - timedelta(days=30),
            status=Doctor.Status.APPROVED.value,
        )
        DoctorSpecialty.objects.create(
            doctor=doctor,
            specialty=self.main_specialty,
            university="Damascus",
        )
        Clinic.objects.create(
            doctor=doctor,
            address="Test Street",
            location=Point(44.2, 32.1, srid=4326),
            phone="011 223 3345",
        )
        self.client.force_authenticate(doctor_user)
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_view_rejects_users_with_non_doctor_role(self):
        self.client.force_authenticate(self.patient_user)
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_view_rejects_unauthenticated_users(self):
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
