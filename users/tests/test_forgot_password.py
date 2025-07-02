from django.contrib.auth.hashers import check_password
from django.urls import reverse

from rest_framework.test import APITestCase
from rest_framework import status

from users.models import CustomUser as User
from users.services import OTPService

otp_service = OTPService()


class ForgetPasswordTests(APITestCase):
    def setUp(self):
        self.path = reverse("forget-password-verify-otp")
        self.send_path = reverse("forget-password-send-otp")
        self.add_password_path = reverse("forget-password-add-otp")

        user_data = {
            "first_name": "John",
            "last_name": "Doe",
            "phone": "0912121212",
            "password": "abcX123#",
            "is_verified_phone": False,
        }
        self.user = User.objects.create_user(**user_data)

    def test_send_otp_successful(self):
        data = {"phone": self.user.phone}
        response = self.client.post(self.send_path, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(
            "تم إرسال رمز التحقق. يرجى التحقق من هاتفك قريبًا.", str(response.data)
        )

    def test_send_otp_fails_on_non_existing_user(self):
        data = {"phone": "0999121882"}
        response = self.client.post(self.send_path, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("رقم الجوال غير موجود", str(response.data))

    def test_verification_successful(self):
        data = {
            "phone": self.user.phone,
            "code": otp_service.generate(
                f"{self.user.id}:forget-password"
            ),
        }
        response = self.client.post(self.path, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access_token", str(response.data))
        self.assertIn("refresh_token", str(response.data))

    def test_verification_fails_on_invalid_code(self):
        data = {
            "phone": self.user.phone,
            "code": 99999,
        }
        response = self.client.post(self.path, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("رمز التحقق غير صالح.", str(response.data))

    def test_add_new_password_successfully(self):
        self.client.force_authenticate(self.user)

        data = {"new_password": "abcX123#OTP"}
        otp = otp_service.generate(f"{self.user.id}:forget-password")
        otp_service.verify_and_mark_as_verified(f"{self.user.id}:forget-password", otp)
        response = self.client.post(self.add_password_path, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("تم تغيير كلمة السر بنجاح", str(response.data))

        self.user.refresh_from_db()

        passwordChanged = check_password(data["new_password"], self.user.password)

        self.assertEqual(passwordChanged, True)
