from django.urls import reverse
from evaluations.models import Evaluation
from evaluations.tests.base import EvaluationBaseTestCase
from rest_framework import status


class EvaluationListTests(EvaluationBaseTestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.path = reverse("evaluation-list-create")
        cls.evaluation = Evaluation.objects.create(
            patient=cls.patient,
            appointment=cls.completed_appointment,
            rate=5,
            comment="Excellent service and very professional doctor.",
        )

    def test_success_patient_list_evaluation(self):
        self.client.force_authenticate(user=self.patient_user)
        response = self.client.get(self.path, data={"clinic_id": self.clinic.pk})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertIn("results", str(data))

    def test_success_doctor_list_evaluation(self):
        self.client.force_authenticate(user=self.doctor_user)
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertIn("results", str(data))

    def test_success_assistant_list_evaluation(self):
        self.client.force_authenticate(user=self.assistant_user)
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertIn("results", str(data))

    def test_success_anonymous_user_list_evaluation(self):
        response = self.client.get(self.path, data={"clinic_id": self.clinic.pk})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertIn("results", str(data))
