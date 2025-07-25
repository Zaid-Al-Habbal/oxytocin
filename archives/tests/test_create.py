from django.utils import timezone
from django.urls import reverse
from appointments.models import Appointment
from rest_framework import status

from .test_base import ArchiveBaseTestCase


class ArchiveCreateTestCase(ArchiveBaseTestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.path = reverse("archive-create", kwargs={"patient_pk": cls.patient_user.pk})
        cls.data = {
            "appointment_id": cls.in_consultation_appointment.pk,
            "main_complaint": "string",
            "case_history": "string",
            "cost": 220.25,
        }

    def test_create_successful(self):
        self.client.force_authenticate(self.doctor_user)
        response = self.client.post(self.path, self.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_fails_on_appointment_not_in_consultation(self):
        completed_appointment = Appointment.objects.create(
            patient=self.patient_user,
            clinic=self.clinic,
            visit_date=timezone.now().date(),
            visit_time=timezone.now().time(),
            status=Appointment.Status.COMPLETED.value,
        )
        self.client.force_authenticate(self.doctor_user)
        data = self.data.copy()
        data["appointment_id"] = completed_appointment.pk
        response = self.client.post(self.path, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_view_rejects_users_with_non_doctor_role(self):
        self.client.force_authenticate(self.patient_user)
        response = self.client.post(self.path, self.data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_view_rejects_unauthenticated_users(self):
        response = self.client.post(self.path, self.data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
