from django.urls import reverse
from rest_framework import status
from django.contrib.gis.geos import Point
from archives.models import Archive
from users.models import CustomUser as User
from patients.models import Patient

from .base import ArchiveBaseTestCase


class ArchiveDestroyTestCase(ArchiveBaseTestCase):

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
        cls.path = reverse("archive-destroy", kwargs={"pk": archive.pk})

    def test_destroy_successful(self):
        self.client.force_authenticate(self.patient_user)
        response = self.client.delete(self.path)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_destroy_fails_on_non_existing(self):
        path = reverse("archive-destroy", kwargs={"pk": 9999})
        self.client.force_authenticate(self.patient_user)
        response = self.client.delete(path)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_view_fails_on_non_own_patient(self):
        path = reverse("archive-destroy", kwargs={"pk": self.archive.pk})
        patient_user = User.objects.create_user(
            phone="0999111199",
            password="abcX123!",
            first_name="Alphonse",
            last_name="Elric",
            role=User.Role.PATIENT.value,
            is_verified_phone=True,
            gender="male",
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
        self.client.force_authenticate(patient_user)
        response = self.client.delete(path)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_view_rejects_users_with_non_patient_role(self):
        self.client.force_authenticate(self.doctor_user)
        response = self.client.delete(self.path)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_view_rejects_unauthenticated_users(self):
        response = self.client.delete(self.path)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
