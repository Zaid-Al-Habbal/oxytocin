from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework.test import APITestCase
from rest_framework import status


User = get_user_model()


class UserCreateTests(APITestCase):
    def test_a_correct_create_view(self):
        """
        Test we can create a new user.
        """
        path = reverse("user-create")
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "phone": "1234567890",
            "email": "test@test.com",
            "image": None,
            "gender": "male",
            "birth_date": "1996-11-22",
            "password": "Password123test!",
            "password_confirm": "Password123test!",
        }
        response = self.client.post(path, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["first_name"], "John")
        self.assertEqual(response.data["last_name"], "Doe")
        self.assertEqual(response.data["phone"], "1234567890")
        self.assertEqual(response.data["email"], "test@test.com")
        self.assertIsNone(response.data["image"])
        self.assertEqual(response.data["gender"], "male")
        self.assertEqual(response.data["birth_date"], "1996-11-22")

    def test_create_work_when_email_is_blank(self):
        """
        Test create work when email is blank (convert it to null).
        """
        path = reverse("user-create")
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "phone": "1234567890",
            "email": " ",
            "image": None,
            "gender": "male",
            "birth_date": "1996-11-22",
            "password": "Password123test!",
            "password_confirm": "Password123test!",
        }
        response = self.client.post(path, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNone(response.data["email"])

    def test_create_fails_when_passwords_do_not_match(self):
        """
        Test create fails with a 400 error when password and password_confirm do not match.
        """
        path = reverse("user-create")
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "phone": "1234567890",
            "email": "test@test.com",
            "image": None,
            "gender": "male",
            "birth_date": "1996-11-22",
            "password": "Password123test!",
            "password_confirm": "Password123test@",
        }
        response = self.client.post(path, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password_confirm", response.data)

    def test_create_fails_when_password_less_than_8(self):
        """
        Test create fails with a 400 error when password less than 8 characters.
        """
        path = reverse("user-create")
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "phone": "1234567890",
            "email": "test@test.com",
            "image": None,
            "gender": "male",
            "birth_date": "1996-11-22",
            "password": "Pass12!",
            "password_confirm": "Pass12!",
        }
        response = self.client.post(path, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)
        password_errors = response.data["password"]
        self.assertTrue(any("8" in msg for msg in password_errors))

    def test_create_fails_when_password_does_not_contain_lowercase(self):
        """
        Test create fails with a 400 error when password does not contain lowercase character.
        """
        path = reverse("user-create")
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "phone": "1234567890",
            "email": "test@test.com",
            "image": None,
            "gender": "male",
            "birth_date": "1996-11-22",
            "password": "PASSWORD123TEST!",
            "password_confirm": "PASSWORD123TEST!",
        }
        response = self.client.post(path, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)
        password_errors = response.data["password"]
        self.assertTrue(any("lowercase" in msg for msg in password_errors))

    def test_create_fails_when_password_does_not_contain_uppercase(self):
        """
        Test create fails with a 400 error when password does not contain uppercase character.
        """
        path = reverse("user-create")
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "phone": "1234567890",
            "email": "test@test.com",
            "image": None,
            "gender": "male",
            "birth_date": "1996-11-22",
            "password": "password123test!",
            "password_confirm": "password123test!",
        }
        response = self.client.post(path, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)
        password_errors = response.data["password"]
        self.assertTrue(any("uppercase" in msg for msg in password_errors))

    def test_create_fails_when_password_does_not_contain_digit(self):
        """
        Test create fails with a 400 error when password does not contain digit.
        """
        path = reverse("user-create")
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "phone": "1234567890",
            "email": "test@test.com",
            "image": None,
            "gender": "male",
            "birth_date": "1996-11-22",
            "password": "Passwordtest!",
            "password_confirm": "Passwordtest!",
        }
        response = self.client.post(path, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)
        password_errors = response.data["password"]
        self.assertTrue(any("number" in msg for msg in password_errors))

    def test_create_fails_when_password_does_not_contain_symbol(self):
        """
        Test create fails with a 400 error when password does not contain symbol.
        """
        path = reverse("user-create")
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "phone": "1234567890",
            "email": "test@test.com",
            "image": None,
            "gender": "male",
            "birth_date": "1996-11-22",
            "password": "Password123test",
            "password_confirm": "Password123test",
        }
        response = self.client.post(path, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)
        password_errors = response.data["password"]
        self.assertTrue(any("special" in msg for msg in password_errors))


class UserDestroyTests(APITestCase):
    def test_destroy_view(self):
        """
        Test we can delete a user.
        """
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
        user = User.objects.create(**user_data)
        path = reverse("user-update-destroy", kwargs={"pk": user.pk})
        response = self.client.delete(path)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
