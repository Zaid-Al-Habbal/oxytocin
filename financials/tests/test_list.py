from django.urls import reverse
from rest_framework import status

from financials.models import Financial

from .base import FinancialBaseTestCase


class FinancialListTestCase(FinancialBaseTestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.path = reverse("financial-list")
        Financial.objects.create(
            clinic=cls.clinic,
            patient=cls.patient,
            cost=300.0,
        )

    def test_patient_list_successful(self):
        self.client.force_authenticate(user=self.patient_user)
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", str(response.data))
        self.assertIn("clinic", str(response.data))

    def test_assistant_list_successful(self):
        self.client.force_authenticate(user=self.assistant_user)
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", str(response.data))
        self.assertIn("patient", str(response.data))

    def test_view_rejects_users_with_doctor_role(self):
        self.client.force_authenticate(self.doctor_user)
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_view_rejects_unauthenticated_users(self):
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
