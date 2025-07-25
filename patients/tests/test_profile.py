from rest_framework.test import APITestCase
from django.contrib.gis.geos import Point
from django.urls import reverse
from users.models import CustomUser as User
from patients.models import Patient
from rest_framework import status


class PatientProfileViewTests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.password = "TestPass123!"
        cls.url = reverse("view-update-patient-profile")

        cls.patient_user = User.objects.create_user(
            phone="0999111122",
            password=cls.password,
            first_name="Patient",
            last_name="User",
            role="patient",
            is_verified_phone=True,
            gender="male",
            birth_date="1995-05-01",
        )

        cls.patient = Patient.objects.create(
            user=cls.patient_user,
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

        cls.doctor_user = User.objects.create_user(
            phone="0988776655",
            password=cls.password,
            first_name="Doctor",
            last_name="User",
            role="doctor",
            is_verified_phone=True,
            gender="male",
            birth_date="1980-01-01",
        )

    def test_get_patient_profile_success(self):
        self.client.force_authenticate(self.patient_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user"]["first_name"], "Patient")
        self.assertEqual(response.data["address"], "Damascus")

    def test_update_patient_profile_success(self):
        self.client.force_authenticate(self.patient_user)
        response = self.client.patch(
            self.url,
            {"address": "Aleppo", "user": {"first_name": "UpdatedName"}},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.patient.refresh_from_db()
        self.assertEqual(self.patient.address, "Aleppo")
        self.assertEqual(self.patient.user.first_name, "UpdatedName")

    def test_unauthenticated_user_cannot_access(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_non_patient_role_cannot_access(self):
        self.client.force_authenticate(self.doctor_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
