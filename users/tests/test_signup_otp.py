from django.urls import reverse
from django.conf import settings

from rest_framework.test import APITestCase
from rest_framework import status

from users.models import CustomUser as User
from users.serializers import SIGNUP_KEY
from users.services import OTPService

otp_service = OTPService()


class SignUpOTPTests(APITestCase):
    def setUp(self):
        self.path = reverse("otp-signup-verify")
        self.send_path = reverse("otp-signup-send")
        user_data = {
            "first_name": "John",
            "last_name": "Doe",
            "phone": f"+963{settings.SAFE_PHONE_NUMBERS[0][1:]}",
            "password": "abcX123#",
            "is_verified_phone": False,
        }
        self.user = User.objects.create_user(**user_data)

    def test_send_sms_successful(self):
        phone = f"0{self.user.phone[4:]}"
        data = {"phone": phone}
        response = self.client.post(self.send_path, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(
            "تم إرسال رمز تسجيل الدخول إليك. يُرجى التحقق من هاتفك قريبًا.",
            str(response.data),
        )

    def test_send_sms_fails_on_non_existing_user(self):
        phone = settings.SAFE_PHONE_NUMBERS[1]
        data = {"phone": phone}
        response = self.client.post(self.send_path, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "يرجى التحقق من رقم الهاتف والمحاولة مرة أخرى.", str(response.data)
        )

    def test_verification_successful(self):
        phone = f"0{self.user.phone[4:]}"
        key = SIGNUP_KEY % {"user": self.user.id}
        data = {
            "phone": phone,
            "code": otp_service.generate(key),
        }
        response = self.client.post(self.path, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access_token", str(response.data))

    def test_verification_fails_on_invalid_code(self):
        phone = f"0{self.user.phone[4:]}"
        data = {
            "phone": phone,
            "code": 99999,
        }
        response = self.client.post(self.path, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("رمز التحقق غير صالح.", str(response.data))

    def test_verification_fails_on_invalid_user(self):
        user = User.objects.create_user(
            first_name="Mary",
            last_name="Hart",
            phone=f"+963{settings.SAFE_PHONE_NUMBERS[1][1:]}",
            password="abcX123#",
            is_verified_phone=False,
        )
        phone = f"0{user.phone[4:]}"
        key = SIGNUP_KEY % {"user": self.user.id}
        data = {
            "phone": phone,
            "code": otp_service.generate(key),
        }
        response = self.client.post(self.path, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("رمز التحقق غير صالح.", str(response.data))

    def test_verification_fails_on_non_existing_user(self):
        phone = settings.SAFE_PHONE_NUMBERS[1]
        key = SIGNUP_KEY % {"user": self.user.id}
        data = {
            "phone": phone,
            "code": otp_service.generate(key),
        }
        response = self.client.post(self.path, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "يرجى التحقق من رقم الهاتف والمحاولة مرة أخرى.", str(response.data)
        )
