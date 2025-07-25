from rest_framework.test import APITestCase
from django.urls import reverse
from users.models import CustomUser as User
from rest_framework import status


class LoginPatientTestCase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.login_url = reverse("login-patient")  # Make sure your url name matches
        cls.password = "StrongPassw0rd!"

        # Verified patient
        cls.patient = User.objects.create_user(
            phone="0999999999",
            password=cls.password,
            first_name="Patient",
            last_name="xxx",
            role="patient",
            is_verified_phone=True,
        )

        # Unverified patient
        cls.unverified_patient = User.objects.create_user(
            phone="0888888888",
            password=cls.password,
            first_name="Unverified",
            last_name="xxx",
            role="patient",
            is_verified_phone=False,
        )

        # A doctor
        cls.doctor = User.objects.create_user(
            phone="0777777777",
            password=cls.password,
            first_name="Doctor",
            last_name="xxx",
            role="doctor",
            is_verified_phone=True,
        )

    def test_login_successful_for_verified_patient(self):
        response = self.client.post(
            self.login_url, {"phone": self.patient.phone, "password": self.password}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_fails_with_wrong_password(self):
        response = self.client.post(
            self.login_url,
            {"phone": self.patient.phone, "password": "WrongPassword123"},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non_field_errors", response.data)

    def test_login_fails_if_not_verified_phone(self):
        response = self.client.post(
            self.login_url,
            {"phone": self.unverified_patient.phone, "password": self.password},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non_field_errors", response.data)
        self.assertIn(
            "الرجاء التحقق من رقم هاتفك أولاً.",
            response.data["non_field_errors"][0].lower(),
        )

    def test_login_fails_if_not_patient(self):
        response = self.client.post(
            self.login_url, {"phone": self.doctor.phone, "password": self.password}
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non_field_errors", response.data)
        self.assertIn(
            "فقط المرضى يستطيعون تسجيل الدحول هنا",
            response.data["non_field_errors"][0].lower(),
        )

    def test_login_fails_with_non_existing_user(self):
        response = self.client.post(
            self.login_url, {"phone": "0000000000", "password": "any"}
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non_field_errors", response.data)
