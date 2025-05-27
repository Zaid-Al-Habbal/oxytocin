from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from users.models import CustomUser as User


class DoctorLoginTests(APITestCase):
    def setUp(self):
        self.path = reverse("doctor-login")
        self.password = "abcX123#"

        self.verified_doctor = User.objects.create_user(
            first_name="verified",
            last_name="doctor",
            phone="0934567899",
            is_verified_phone=True,
            password=self.password,
            role=User.Role.DOCTOR,
        )

        self.unverified_doctor = User.objects.create_user(
            first_name="unverified",
            last_name="doctor",
            phone="0987654324",
            is_verified_phone=False,
            password=self.password,
            role=User.Role.DOCTOR,
        )

        self.patient = User.objects.create_user(
            first_name="patient",
            last_name="patient",
            phone="0922334455",
            is_verified_phone=True,
            password=self.password,
            role=User.Role.PATIENT,
        )

    def test_successful_if_doctor_phone_is_verified(self):
        data = {
            "phone": self.verified_doctor.phone,
            "password": self.password,
        }
        response = self.client.post(self.path, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access_token", response.data)
        self.assertIn("refresh_token", response.data)
        self.assertIn("expires_in", response.data)

    def test_fails_if_doctor_phone_is_not_verified(self):
        data = {
            "phone": self.unverified_doctor.phone,
            "password": self.password,
        }
        response = self.client.post(self.path, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("الرجاء التحقق من رقم هاتفك أولاً.", str(response.data))

    def test_fails_if_user_role_is_not_doctor(self):
        data = {
            "phone": self.patient.phone,
            "password": self.password,
        }
        response = self.client.post(self.path, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non_field_errors", response.data)
        self.assertIn("بيانات اعتماد خاطئة!", str(response.data))

    def test_login_with_wrong_password(self):
        data = {
            "phone": self.verified_doctor.phone,
            "password": "Wr0ng_Passw0rd",
        }
        response = self.client.post(self.path, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non_field_errors", response.data)
        self.assertIn("بيانات اعتماد خاطئة!", str(response.data))

    def test_login_with_non_existing_user(self):
        data = {
            "phone": "0922222222",
            "password": self.password,
        }
        response = self.client.post(self.path, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non_field_errors", response.data)
        self.assertIn("بيانات اعتماد خاطئة!", str(response.data))
