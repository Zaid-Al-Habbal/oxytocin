from rest_framework.test import APITestCase
from django.urls import reverse
from users.models import CustomUser as User
from rest_framework import status
from assistants.models import Assistant


class CompleteAssistantRegistrationTests(APITestCase):
    def setUp(self):
        self.password = "StrongPassw0rd!"
        self.url = reverse('complete-assistant-registeration')  # update this if needed
        
        self.verified_assistant = User.objects.create_user(
            phone="0999999999",
            password=self.password,
            first_name="Assistant",
            last_name="One",
            birth_date="1995-05-01",
            gender="male",
            is_verified_phone=True,
            role="assistant"
        )

        self.doctor_user = User.objects.create_user(
            phone="0777777777",
            password=self.password,
            first_name="Dr",
            last_name="User",
            birth_date="1980-01-01",
            gender="male",
            is_verified_phone=True,
            role="doctor"
        )
        self.payload = {
            "user": {
                "gender": "male",
                "birth_date": "1995-05-01",
            },
            "about": "....",
            "education": "my education",
            "start_work_date": "2020-2-2"
        }

    def test_successful_assistant_profile_creation(self):
        self.client.force_authenticate(self.verified_assistant)

        response = self.client.post(self.url, self.payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Assistant.objects.filter(user=self.verified_assistant).exists())

    def test_cannot_create_profile_if_already_exists(self):
        Assistant.objects.create(user=self.verified_assistant, education="my education", start_work_date="2020-2-2")

        self.client.force_authenticate(self.verified_assistant)

        response = self.client.post(self.url, self.payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("لقد قمت بإنشاء ملف مساعد من قبل", str(response.data))

    def test_reject_if_phone_not_verified(self):
        self.verified_assistant.is_verified_phone = False
        self.verified_assistant.save()
        self.client.force_authenticate(self.verified_assistant)

        response = self.client.post(self.url, self.payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("لم يتم التحقق من رقم الهاتف.", str(response.data))

    def test_reject_if_user_is_not_assistant(self):
        self.client.force_authenticate(self.doctor_user)

        response = self.client.post(self.url, self.payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("ليس لديك الصلاحيات لإكمال هذه العملية", str(response.data))
        
    def test_unauthenticated_user_cannot_access(self):
        response = self.client.post(self.url, self.payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

