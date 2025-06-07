from django.urls import reverse

from rest_framework.test import APITestCase
from rest_framework import status

from common.utils import generate_test_image

from users.models import CustomUser as User


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
            "is_verified_phone": True,
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
