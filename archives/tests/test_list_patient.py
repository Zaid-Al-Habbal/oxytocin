from django.urls import reverse
from rest_framework import status

from .base import ArchiveBaseTestCase


class ArchivePatientListTestCase(ArchiveBaseTestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.path = reverse("patient-archive-list")

    def test_list_successful(self):
        self.client.force_authenticate(self.patient_user)
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertIn("results", str(data))

    def test_view_rejects_users_with_non_patient_role(self):
        self.client.force_authenticate(self.doctor_user)
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_view_rejects_unauthenticated_users(self):
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
