from django.urls import reverse

from rest_framework.test import APITestCase
from rest_framework import status

from users.models import CustomUser as User


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
