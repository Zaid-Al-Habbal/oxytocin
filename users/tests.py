from django.urls import reverse

from rest_framework.test import APITestCase
from rest_framework import status

from common.utils import generate_test_image

from .models import CustomUser as User
from .services import OTPService

otp_service = OTPService()


class UserCreateTests(APITestCase):
    def setUp(self):
        self.path = reverse("user-create-destroy")

    def test_a_correct_create_view(self):
        """
        Test we can create a new user.
        """
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "phone": "1234567890",
            "password": "Password123test!",
            "password_confirm": "Password123test!",
        }
        response = self.client.post(self.path, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["first_name"], "John")
        self.assertEqual(response.data["last_name"], "Doe")
        self.assertEqual(response.data["phone"], data["phone"])

    def test_create_fails_when_passwords_do_not_match(self):
        """
        Test create fails with a 400 error when password and password_confirm do not match.
        """
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "phone": "1234567890",
            "password": "Password123test!",
            "password_confirm": "Password123test@",
        }
        response = self.client.post(self.path, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password_confirm", response.data)

    def test_create_fails_when_password_less_than_8(self):
        """
        Test create fails with a 400 error when password less than 8 characters.
        """
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "phone": "1234567890",
            "password": "Pass12!",
            "password_confirm": "Pass12!",
        }
        response = self.client.post(self.path, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)
        password_errors = response.data["password"]
        self.assertTrue(any("8" in msg for msg in password_errors))

    def test_create_fails_when_password_does_not_contain_lowercase(self):
        """
        Test create fails with a 400 error when password does not contain lowercase character.
        """
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "phone": "1234567890",
            "password": "PASSWORD123TEST!",
            "password_confirm": "PASSWORD123TEST!",
        }
        response = self.client.post(self.path, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)
        self.assertIn(
            "كلمة السر يجب أن تحوي على حرف صغير واحد على الأقل.",
            str(response.data),
        )

    def test_create_fails_when_password_does_not_contain_uppercase(self):
        """
        Test create fails with a 400 error when password does not contain uppercase character.
        """
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "phone": "1234567890",
            "password": "password123test!",
            "password_confirm": "password123test!",
        }
        response = self.client.post(self.path, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)
        self.assertIn(
            "كلمة السر يجب أن تحوي على حرف كبير واحد على الأقل.", str(response.data)
        )

    def test_create_fails_when_password_does_not_contain_digit(self):
        """
        Test create fails with a 400 error when password does not contain digit.
        """
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "phone": "1234567890",
            "password": "Passwordtest!",
            "password_confirm": "Passwordtest!",
        }
        response = self.client.post(self.path, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)
        self.assertIn(
            "كلمة السر يجب أن تحوي على رقم واحد على الأقل.", str(response.data)
        )

    def test_create_fails_when_password_does_not_contain_symbol(self):
        """
        Test create fails with a 400 error when password does not contain symbol.
        """
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "phone": "1234567890",
            "password": "Password123test",
            "password_confirm": "Password123test",
        }
        response = self.client.post(self.path, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)
        self.assertIn(
            "(!@#$%^&*()_-+=) كلمة السر يجب أن تحوي على أحد الرموز التالية على أقل.",
            str(response.data),
        )


class UserDestroyTests(APITestCase):
    def setUp(self):
        self.path = reverse("user-create-destroy")
        user_data = {
            "first_name": "John",
            "last_name": "Doe",
            "phone": "1234567890",
            "email": "test@test.com",
            "image": None,
            "gender": "male",
            "birth_date": "1996-11-22",
            "password": "Password123test",
        }
        self.user = User.objects.create_user(**user_data)

    def test_successful_destroy(self):
        self.client.force_authenticate(self.user)
        response = self.client.delete(self.path)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_successful_soft_destroy_for_doctor(self):
        self.user.role = User.Role.DOCTOR
        self.user.save()
        self.client.force_authenticate(self.user)
        response = self.client.delete(self.path)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.deleted_at)

    def test_fails_on_unauthenticated_user(self):
        response = self.client.delete(self.path)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserImageTests(APITestCase):
    def setUp(self):
        self.path = reverse("user-image")
        user_data = {
            "first_name": "John",
            "last_name": "Doe",
            "phone": "1234567890",
            "email": "test@test.com",
            "gender": "male",
            "birth_date": "1996-11-22",
            "password": "Password123test",
        }
        self.user = User.objects.create_user(**user_data)
        self.data = {"image": generate_test_image()}

    def test_successful_image_upload(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.path, self.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("image", str(response.data))

    def test_fails_on_unverified_phone(self):
        self.user.is_verified_phone = False
        self.user.save()
        self.client.force_authenticate(self.user)
        response = self.client.post(self.path, self.data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("لم يتم التحقق من رقم الهاتف.", str(response.data))

    def test_fails_on_unauthenticated_users(self):
        response = self.client.post(self.path, self.data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserPhoneVerificationTests(APITestCase):
    def setUp(self):
        self.path = reverse("user-phone-verification")
        self.send_path = reverse("user-phone-verification-send")
        user_data = {
            "first_name": "John",
            "last_name": "Doe",
            "phone": "0000",
            "password": "abcX123#",
            "is_verified_phone": False,
        }
        self.user = User.objects.create_user(**user_data)

    def test_send_sms_successful(self):
        data = {"user_id": self.user.id}
        response = self.client.post(self.send_path, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(
            "تم إرسال رمز التحقق. يرجى التحقق من هاتفك قريبًا.", str(response.data)
        )

    def test_send_sms_fails_on_non_existing_user(self):
        data = {"user_id": 9999999}
        response = self.client.post(self.send_path, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("العنصر غير موجود", str(response.data))

    def test_verification_successful(self):
        data = {
            "user_id": self.user.id,
            "verification_code": otp_service.generate(self.user.id),
        }
        response = self.client.post(self.path, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access_token", str(response.data))

    def test_verification_fails_on_invalid_code(self):
        data = {
            "user_id": self.user.id,
            "verification_code": 99999,
        }
        response = self.client.post(self.path, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("رمز التحقق غير صالح.", str(response.data))

    def test_verification_fails_on_invalid_user(self):
        user = User.objects.create_user(
            first_name="Mary",
            last_name="Hart",
            phone="00000",
            password="abcX123#",
            is_verified_phone=False,
        )
        data = {
            "user_id": user.id,
            "verification_code": otp_service.generate(self.user.id),
        }
        response = self.client.post(self.path, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("رمز التحقق غير صالح.", str(response.data))

    def test_verification_fails_on_non_existing_user(self):
        data = {
            "user_id": 99999999999999,
            "verification_code": otp_service.generate(self.user.id),
        }
        response = self.client.post(self.path, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("العنصر غير موجود", str(response.data))
