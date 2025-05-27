from django.urls import reverse
from django.utils import timezone

from datetime import timedelta
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import CustomUser as User

from doctors.models import Doctor, Specialty

from common.utils import generate_test_pdf


class DoctorCreateTests(APITestCase):
    def setUp(self):
        self.path = reverse("doctor-create")
        self.password = "abcX123#"

        self.verified_doctor = User.objects.create_user(
            first_name="verified",
            last_name="doctor",
            phone="0921341239",
            is_verified_phone=True,
            password=self.password,
            role=User.Role.DOCTOR,
        )

        self.unverified_doctor = User.objects.create_user(
            first_name="unverified",
            last_name="doctor",
            phone="0921341240",
            is_verified_phone=False,
            password=self.password,
            role=User.Role.DOCTOR,
        )

        self.patient = User.objects.create_user(
            first_name="patient",
            last_name="patient",
            phone="0921341241",
            is_verified_phone=True,
            password=self.password,
            role=User.Role.PATIENT,
        )

        specialty1 = Specialty.objects.create(name="Test1")
        specialty2 = Specialty.objects.create(name="Test2", parent=specialty1)

        self.data = {
            "user.gender": "male",
            "user.birth_date": "1999-09-19",
            "about": "A test about",
            "education": "about education",
            "start_work_date": timezone.now().date() - timedelta(days=30),
            "certificate": generate_test_pdf(),
            "specialties[0]specialty": specialty1.name,
            "specialties[0]university": "Test1 university",
            "specialties[1]specialty": specialty2.name,
            "specialties[1]university": "Test2 university",
        }

    def test_successful_doctor_creation(self):
        self.client.force_authenticate(self.verified_doctor)
        response = self.client.post(self.path, self.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Doctor.objects.filter(user=self.verified_doctor).exists())
        self.assertIn("user", str(response.data))
        self.assertIn("gender", str(response.data))
        self.assertIn("birth_date", str(response.data))
        self.assertIn("about", str(response.data))
        self.assertIn("education", str(response.data))
        self.assertIn("start_work_date", str(response.data))
        self.assertIn("status", str(response.data))
        self.assertIn("specialties", str(response.data))
        self.assertIn("specialty", str(response.data))
        self.assertIn("university", str(response.data))
        self.assertIn("created_at", str(response.data))
        self.assertIn("updated_at", str(response.data))

    def test_fails_if_doctor_already_exists(self):
        data = self.data.copy()
        data.pop("user.gender")
        data.pop("user.birth_date")
        data.pop("specialties[0]specialty")
        data.pop("specialties[0]university")
        data.pop("specialties[1]specialty")
        data.pop("specialties[1]university")
        Doctor.objects.create(user=self.verified_doctor, **data)

        self.client.force_authenticate(self.verified_doctor)

        self.data["certificate"] = generate_test_pdf()
        response = self.client.post(self.path, self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("لديك حساب طبيب بالفعل.", str(response.data))

    def test_fails_if_phone_is_not_verified(self):
        self.client.force_authenticate(self.unverified_doctor)
        response = self.client.post(self.path, self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("لم يتم التحقق من رقم الهاتف.", str(response.data))

    def test_fails_if_user_role_is_not_doctor(self):
        self.client.force_authenticate(self.patient)
        response = self.client.post(self.path, self.data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("ليس لديك الدور المطلوب.", str(response.data))

    def test_fails_if_unauthenticated_user_try_to_access(self):
        response = self.client.post(self.path, self.data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
