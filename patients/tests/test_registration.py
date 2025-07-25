from rest_framework.test import APITestCase
from django.contrib.gis.geos import Point
from django.urls import reverse
from users.models import CustomUser as User
from patients.models import Patient
from rest_framework import status


class CompletePatientRegistrationTests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.password = "StrongPassw0rd!"
        cls.url = reverse("complete-register-patient")  # update this if needed

        cls.verified_patient = User.objects.create_user(
            phone="0999999999",
            password=cls.password,
            first_name="Patient",
            last_name="One",
            birth_date="1995-05-01",
            gender="male",
            is_verified_phone=True,
            role="patient",
        )

        cls.unverified_patient = User.objects.create_user(
            phone="0888888888",
            password=cls.password,
            first_name="Patient2",
            last_name="Two",
            birth_date="1992-02-02",
            gender="female",
            is_verified_phone=False,
            role="patient",
        )

        cls.doctor_user = User.objects.create_user(
            phone="0777777777",
            password=cls.password,
            first_name="Dr",
            last_name="User",
            birth_date="1980-01-01",
            gender="male",
            is_verified_phone=True,
            role="doctor",
        )
        cls.payload = {
            "user": {
                "first_name": "NewFirstName",
                "last_name": "NewLastName",
                "gender": "male",
                "birth_date": "1995-05-01",
            },
            "address": "Damascus",
            "longitude": "36.29128",
            "latitude": "33.513806",
            "job": "Engineer",
            "blood_type": "A+",
            "medical_history": "None",
            "surgical_history": "",
            "allergies": "Peanuts",
            "medicines": "",
            "is_smoker": False,
            "is_drinker": False,
            "is_married": False,
        }

    def test_successful_patient_profile_creation(self):
        self.client.force_authenticate(self.verified_patient)

        response = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Patient.objects.filter(user=self.verified_patient).exists())

    def test_cannot_create_profile_if_already_exists(self):
        Patient.objects.create(
            user=self.verified_patient,
            address="Damascus",
            location=Point(36.29, 33.51, srid=4326),
        )

        self.client.force_authenticate(self.verified_patient)

        response = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("لقد قمت بإنشاء ملف شخصي سابقا", str(response.data))

    def test_reject_if_phone_not_verified(self):
        self.client.force_authenticate(self.unverified_patient)

        response = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("لم يتم التحقق من رقم الهاتف.", str(response.data))

    def test_reject_if_user_is_not_patient(self):
        self.client.force_authenticate(self.doctor_user)

        response = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("ليس لديك الصلاحيات لإكمال هذه العملية", str(response.data))

    def test_unauthenticated_user_cannot_access(self):
        response = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
