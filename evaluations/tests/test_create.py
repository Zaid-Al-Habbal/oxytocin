from django.contrib.gis.geos import Point
from django.utils import timezone

from django.urls import reverse
from rest_framework import status
from appointments.models import Appointment
from evaluations.models import Evaluation
from evaluations.tests.base import EvaluationBaseTestCase
from patients.models import Patient
from users.models import CustomUser as User


class EvaluationCreateTests(EvaluationBaseTestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.path = reverse("evaluation-list-create")
        cls.patient_user_2 = User.objects.create_user(
            phone="0999111131",
            password="abcX123!",
            first_name="Zora",
            last_name="Ideale",
            role=User.Role.PATIENT.value,
            is_verified_phone=True,
            gender="male",
            birth_date="1995-05-01",
        )
        Patient.objects.create(
            user=cls.patient_user_2,
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
        cls.evaluated_appointment = Appointment.objects.create(
            patient=cls.patient_user,
            clinic=cls.clinic,
            visit_date=timezone.now().date(),
            visit_time=timezone.now().time(),
            status=Appointment.Status.COMPLETED.value,
        )
        Evaluation.objects.create(
            patient=cls.patient,
            appointment=cls.evaluated_appointment,
            rate=5,
            comment="Excellent service and very professional doctor.",
        )

    def test_success_create_evaluation(self):
        self.client.force_authenticate(user=self.patient_user)
        response = self.client.post(
            self.path,
            data={
                "appointment_id": self.completed_appointment.pk,
                "rate": 5,
                "comment": "Excellent service and very professional doctor.",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_failed_create_evaluation_using_in_consultation_appointment(self):
        self.client.force_authenticate(user=self.patient_user)
        response = self.client.post(
            self.path,
            data={
                "appointment_id": self.in_consultation_appointment.pk,
                "rate": 5,
                "comment": "Excellent service and very professional doctor.",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_failed_create_evaluation_using_already_evaluated_appointment(self):
        self.client.force_authenticate(user=self.patient_user)
        response = self.client.post(
            self.path,
            data={
                "appointment_id": self.evaluated_appointment.pk,
                "rate": 5,
                "comment": "Excellent service and very professional doctor.",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_failed_create_evaluation_using_other_patient_appointment(self):
        self.client.force_authenticate(user=self.patient_user_2)
        response = self.client.post(
            self.path,
            data={
                "appointment_id": self.completed_appointment.pk,
                "rate": 5,
                "comment": "Excellent service and very professional doctor.",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.data
        self.assertIn("لا يمكنك تقييم هذا الموعد.", str(data))

    def test_view_rejects_users_with_non_patient_role(self):
        self.client.force_authenticate(self.doctor_user)
        response = self.client.post(
            self.path,
            data={
                "appointment_id": self.completed_appointment.pk,
                "rate": 5,
                "comment": "Excellent service and very professional doctor.",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_view_rejects_unauthenticated_users(self):
        response = self.client.post(
            self.path,
            data={
                "appointment_id": self.completed_appointment.pk,
                "rate": 5,
                "comment": "Excellent service and very professional doctor.",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
