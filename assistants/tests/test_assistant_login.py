from rest_framework.test import APITestCase
from django.urls import reverse
from users.models import CustomUser as User
from rest_framework import status


class LoginAssistantTestCase(APITestCase):
    def setUp(self):
        self.login_url = reverse('login-assistant')  # Make sure your url name matches
        self.password = "StrongPassw0rd!"

        # Verified assistant
        self.assistant = User.objects.create_user(
            phone="0999999999",
            password=self.password,
            first_name="assistant",
            last_name='xxx',
            role='assistant',
            is_verified_phone=True
        )

        # A doctor
        self.doctor = User.objects.create_user(
            phone="0777777777",
            password=self.password,
            first_name="Doctor",
            last_name='xxx',
            role='doctor',
            is_verified_phone=True
        )

    def test_login_successful_for_verified_assistant(self):
        response = self.client.post(self.login_url, {
            "phone": self.assistant.phone,
            "password": self.password
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_fails_with_wrong_password(self):
        response = self.client.post(self.login_url, {
            "phone": self.assistant.phone,
            "password": "WrongPassword123"
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non_field_errors", response.data)

    def test_login_fails_if_not_verified_phone(self):
        self.assistant.is_verified_phone = False
        self.assistant.save()
        response = self.client.post(self.login_url, {
            "phone": self.assistant.phone,
            "password": self.password
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non_field_errors", response.data)
        self.assertIn("الرجاء التحقق من رقم هاتفك أولاً.", response.data["non_field_errors"][0].lower())

    def test_login_fails_if_not_assistant(self):
        response = self.client.post(self.login_url, {
            "phone": self.doctor.phone,
            "password": self.password
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non_field_errors", response.data)
        self.assertIn("فقط المساعدات يستطيعون تسجيل الدخول هنا", response.data["non_field_errors"][0].lower())

    def test_login_fails_with_non_existing_user(self):
        response = self.client.post(self.login_url, {
            "phone": "0000000000",
            "password": "any"
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non_field_errors", response.data)

