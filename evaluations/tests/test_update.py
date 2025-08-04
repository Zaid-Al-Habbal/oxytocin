from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from appointments.models import Appointment
from evaluations.models import Evaluation
from evaluations.tests.base import EvaluationBaseTestCase
from rest_framework import status


class EvaluationUpdateTests(EvaluationBaseTestCase):

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

    def test_success_update_evaluation(self):
        self.client.force_authenticate(user=self.patient_user)
        response = self.client.patch(self.path, data={"rate": 4})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertEqual(data["rate"], 4)

    def test_failed_update_evaluation_using_invalid_pk(self):
        self.client.force_authenticate(user=self.patient_user)
        path = reverse("evaluation-retrieve-update", kwargs={"pk": 999999999999})
        response = self.client.patch(path, data={"rate": 4})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_failed_update_evaluation_after_24_hours(self):
        self.client.force_authenticate(user=self.patient_user)
        appointment = Appointment.objects.create(
            patient=self.patient_user,
            clinic=self.clinic,
            visit_date=timezone.now().date(),
            visit_time=timezone.now().time(),
            actual_start_time=timezone.now().time(),
            actual_end_time=timezone.now().time(),
            status=Appointment.Status.COMPLETED,
        )
        evaluation = Evaluation.objects.create(
            patient=self.patient,
            appointment=appointment,
            rate=5,
            comment="Excellent service and very professional doctor.",
        )
        evaluation.created_at = timezone.now() - timedelta(hours=25)
        evaluation.save(force_update=True)
        path = reverse(
            "evaluation-retrieve-update",
            kwargs={"pk": evaluation.pk},
        )
        response = self.client.patch(path, data={"rate": 4})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_view_rejects_users_with_non_patient_role(self):
        self.client.force_authenticate(self.doctor_user)
        response = self.client.patch(self.path, data={"rate": 4})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_view_rejects_unauthenticated_users(self):
        response = self.client.patch(self.path, data={"rate": 4})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
