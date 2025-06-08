from django.core.cache import cache
from django.urls import reverse
from django.conf import settings

from rest_framework.test import APITestCase
from rest_framework import status

from users.models import CustomUser as User
from users.serializers import CHANGE_PHONE_KEY, NEW_PHONE_KEY
from users.services import OTPService

otp_service = OTPService()


class ChangePhoneOTPTests(APITestCase):
    def setUp(self):
        self.send_path = reverse("otp-change-phone-send")
        self.path = reverse("otp-change-phone-verify")
        user_data = {
            "first_name": "John",
            "last_name": "Doe",
            "phone": settings.SAFE_PHONE_NUMBERS[0],
            "password": "abcX123#",
            "is_verified_phone": False,
        }
        self.user = User.objects.create_user(**user_data)

    def test_send_sms_successful(self):
        self.client.force_authenticate(self.user)
        phone = settings.SAFE_PHONE_NUMBERS[1]
        data = {"phone": phone}
        response = self.client.post(self.send_path, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(
            "تم إرسال رمز تغيير رقم هاتفك. يُرجى التحقق من هاتفك قريبًا.",
            str(response.data),
        )

    def test_send_sms_fails_on_same_number(self):
        self.client.force_authenticate(self.user)
        data = {"phone": self.user.phone}
        response = self.client.post(self.send_path, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "يجب أن يكون رقم الهاتف الجديد مختلفًا عن رقم هاتفك الحالي.",
            str(response.data),
        )

    def test_send_sms_fails_on_non_unique_number(self):
        self.client.force_authenticate(self.user)
        user_data = {
            "first_name": "John",
            "last_name": "Doe",
            "phone": settings.SAFE_PHONE_NUMBERS[1],
            "password": "abcX123#",
            "is_verified_phone": False,
        }
        user = User.objects.create_user(**user_data)
        data = {"phone": user.phone}
        response = self.client.post(self.send_path, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("يجب أن يكون هذا الحقل فريدًا.", str(response.data))

    def test_verification_successful(self):
        self.client.force_authenticate(self.user)
        key = CHANGE_PHONE_KEY % {"user": self.user.id}
        data = {"code": otp_service.generate(key)}
        key = NEW_PHONE_KEY % {"user": self.user.id}
        phone = settings.SAFE_PHONE_NUMBERS[1]
        cache.set(key, phone, 360)
        response = self.client.post(self.path, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("phone", str(response.data))

    def test_verification_fails_on_invalid_code(self):
        self.client.force_authenticate(self.user)
        data = {"code": 99999}
        response = self.client.post(self.path, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("رمز التحقق غير صالح.", str(response.data))

    def test_verification_fails_on_on_unauthenticated_user(self):
        phone = settings.SAFE_PHONE_NUMBERS[1]
        key = CHANGE_PHONE_KEY % {"user": self.user.id}
        data = {"code": otp_service.generate(key)}
        key = NEW_PHONE_KEY % {"user": self.user.id}
        phone = settings.SAFE_PHONE_NUMBERS[1]
        cache.set(key, phone, 360)
        response = self.client.post(self.path, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
