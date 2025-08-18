from django.urls import reverse
from rest_framework import status

from financials.models import Financial

from .base import FinancialBaseTestCase


class FinancialUpdateTestCase(FinancialBaseTestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.financial = Financial.objects.create(
            clinic=cls.clinic,
            patient=cls.patient,
            cost=300.0,
        )
        cls.path = reverse("financial-retrieve-update", args=[cls.financial.pk])
        cls.data = {"cost": 50.0}

    def test_update_successful(self):
        self.client.force_authenticate(user=self.assistant_user)
        response = self.client.put(self.path, self.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["cost"], self.financial.cost - self.data["cost"])

    def test_view_rejects_users_with_non_assistant_role(self):
        self.client.force_authenticate(self.patient_user)
        response = self.client.put(self.path, self.data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_view_rejects_unauthenticated_users(self):
        response = self.client.put(self.path, self.data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
