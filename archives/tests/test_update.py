from datetime import timedelta
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from django.contrib.gis.geos import Point
from archives.models import Archive
from clinics.models import Clinic
from common.utils import generate_test_pdf
from doctors.models import Doctor, DoctorSpecialty
from users.models import CustomUser as User

from .base import ArchiveBaseTestCase


class ArchiveUpdateTestCase(ArchiveBaseTestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        archive = Archive.objects.create(
            patient=cls.patient,
            doctor=cls.doctor,
            appointment=cls.in_consultation_appointment,
            specialty=cls.main_specialty,
            main_complaint="string",
            case_history="string",
            cost=10.0,
        )
        cls.non_own_doctor_user = User.objects.create_user(
            phone="0999111118",
            password="abcX123!",
            first_name="Edward",
            last_name="Elric",
            role=User.Role.DOCTOR.value,
            is_verified_phone=True,
            gender="male",
            birth_date="1995-05-01",
        )
        doctor = Doctor.objects.create(
            user=cls.non_own_doctor_user,
            about="About Test",
            education="Test",
            certificate=generate_test_pdf(),
            start_work_date=timezone.now().date() - timedelta(days=30),
            status=Doctor.Status.APPROVED.value,
        )
        DoctorSpecialty.objects.create(
            doctor=doctor,
            specialty=cls.main_specialty,
            university="Damascus",
        )
        cls.clinic = Clinic.objects.create(
            doctor=doctor,
            address="Test Street",
            location=Point(44.2, 32.1, srid=4326),
            phone="011 223 3351",
        )
        cls.path = reverse("archive-update", kwargs={"pk": archive.pk})
        cls.data = {
            "main_complaint": "string",
            "case_history": "string",
        }

    def test_update_successful(self):
        self.client.force_authenticate(self.doctor_user)
        response = self.client.patch(self.path, self.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_view_rejects_non_in_consultation_appointment(self):
        path = reverse("archive-update", kwargs={"pk": self.archive.pk})
        self.client.force_authenticate(self.doctor_user)
        response = self.client.patch(path, self.data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_view_rejects_non_own_doctor(self):
        self.client.force_authenticate(self.non_own_doctor_user)
        response = self.client.patch(self.path, self.data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_view_rejects_users_with_non_doctor_role(self):
        self.client.force_authenticate(self.patient_user)
        response = self.client.patch(self.path, self.data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_view_rejects_unauthenticated_users(self):
        response = self.client.patch(self.path, self.data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
