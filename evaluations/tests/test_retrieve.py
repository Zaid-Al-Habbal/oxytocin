from django.urls import reverse

from rest_framework import status

from evaluations.models import Evaluation
from evaluations.tests.base import EvaluationBaseTestCase


class EvaluationRetrieveTests(EvaluationBaseTestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.evaluation = Evaluation.objects.create(
            patient=cls.patient,
            appointment=cls.completed_appointment,
            rate=5,
            comment="Excellent service and very professional doctor.",
        )
        cls.path = reverse(
            "evaluation-retrieve-update",
            kwargs={"pk": cls.evaluation.pk},
        )

    def test_success_retrieve_evaluation(self):
        self.client.force_authenticate(user=self.patient_user)
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertIn("id", str(data))
        self.assertIn("patient", str(data))
        self.assertIn("appointment", str(data))
        self.assertIn("rate", str(data))
        self.assertIn("comment", str(data))

    def test_failed_retrieve_evaluation_using_invalid_pk(self):
        self.client.force_authenticate(user=self.patient_user)
        path = reverse("evaluation-retrieve-update", kwargs={"pk": 999999999999})
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_failed_retrieve_evaluation_using_non_patient_role(self):
        self.client.force_authenticate(user=self.doctor_user)
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_failed_retrieve_evaluation_using_unauthenticated_user(self):
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
