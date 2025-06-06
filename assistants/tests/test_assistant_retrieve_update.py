from rest_framework.test import APITestCase
from django.urls import reverse
from users.models import CustomUser as User
from rest_framework import status
from django.test import override_settings
from assistants.models import Assistant


class AssistantProfileViewTests(APITestCase):
    def setUp(self):
        self.password = "TestPass123!"
        self.url = reverse("view-update-assistant-profile")

        self.assistant_user = User.objects.create_user(
            phone="0999111122",
            password=self.password,
            first_name="Assistant",
            last_name="User",
            role="assistant",
            is_verified_phone=True,
            gender="male",
            birth_date="1995-05-01"
        )

        self.assistant = Assistant.objects.create(
            user=self.assistant_user,
            about="good assistant",
            education="Management degree",
            start_work_date="2020-2-2"
        )

        self.doctor_user = User.objects.create_user(
            phone="0988776655",
            password=self.password,
            first_name="Doctor",
            last_name="User",
            role="doctor",
            is_verified_phone=True,
            gender="male",
            birth_date="1980-01-01"
        )

    def test_get_assistant_profile_success(self):
        self.client.force_authenticate(self.assistant_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user"]["first_name"], "Assistant")
        self.assertEqual(response.data["education"], "Management degree")

    def test_update_assistant_profile_success(self):
        self.client.force_authenticate(self.assistant_user)
        response = self.client.patch(self.url, {
            "education": "Economy",
            "user": {
                "first_name": "UpdatedName"
            }
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assistant.refresh_from_db()
        self.assertEqual(self.assistant.education, "Economy")
        self.assertEqual(self.assistant.user.first_name, "UpdatedName")

    def test_unauthenticated_user_cannot_access(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_non_assistant_role_cannot_access(self):
        self.client.force_authenticate(self.doctor_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
