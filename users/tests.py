from django.urls import reverse

from rest_framework.test import APITestCase
from rest_framework import status

from .models import CustomUser as User


class UserCreateTests(APITestCase):
    def setUp(self):
        self.path = reverse("user-create")

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
        self.assertEqual(response.data["phone"], "1234567890")

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
    def test_successful_destroy_view(self):
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
        user = User.objects.create_user(**user_data)
        self.client.force_authenticate(user)
        path = reverse("user-destroy", kwargs={"pk": user.pk})
        response = self.client.delete(path)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_fails_on_unauthenticated_user(self):
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
        user = User.objects.create_user(**user_data)
        path = reverse("user-destroy", kwargs={"pk": user.pk})
        response = self.client.delete(path)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
