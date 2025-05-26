from django.urls import reverse
from django.utils import timezone

from datetime import timedelta
from rest_framework import status
from rest_framework.test import APITestCase

from doctors.tests import generate_test_pdf

from users.models import CustomUser as User
from doctors.models import Doctor, Specialty, DoctorSpecialty

from clinics.models import Clinic


class ClinicTests(APITestCase):

    def setUp(self):
        self.create_path = reverse("clinic-create")
        self.retrieve_update_path = reverse("clinic-retrieve-update")
        self.password = "abcX123#"

        self.user = User.objects.create_user(
            first_name="user",
            last_name="without doctor profile",
            phone="0934567890",
            is_verified_phone=True,
            password=self.password,
            role=User.Role.DOCTOR,
        )

        self.user_doctor_clinic = User.objects.create_user(
            first_name="doctor",
            last_name="clinic",
            phone="0934567891",
            is_verified_phone=True,
            password=self.password,
            role=User.Role.DOCTOR,
        )

        self.user_doctor = User.objects.create_user(
            first_name="no clinic",
            last_name="doctor",
            phone="0934567892",
            is_verified_phone=True,
            password=self.password,
            role=User.Role.DOCTOR,
        )

        doctor_data = {
            "about": "About Test",
            "education": "Test",
            "start_work_date": timezone.now().date() - timedelta(days=30),
            "certificate": generate_test_pdf(),
            "status": Doctor.Status.APPROVED,
        }
        self.doctor_with_clinic = Doctor.objects.create(
            user=self.user_doctor_clinic,
            **doctor_data,
        )
        self.doctor_without_clinic = Doctor.objects.create(
            user=self.user_doctor,
            **doctor_data,
        )

        specialty1 = Specialty.objects.create(name="Test1")
        specialty2 = Specialty.objects.create(name="Test2", parent=specialty1)
        specialties = [
            DoctorSpecialty(
                doctor=self.doctor_with_clinic,
                specialty=specialty1,
                university="Damascus",
            ),
            DoctorSpecialty(
                doctor=self.doctor_with_clinic,
                specialty=specialty2,
                university="Tokyo",
            ),
            DoctorSpecialty(
                doctor=self.doctor_without_clinic,
                specialty=specialty1,
                university="Tokyo",
            ),
            DoctorSpecialty(
                doctor=self.doctor_without_clinic,
                specialty=specialty2,
                university="London",
            ),
        ]
        DoctorSpecialty.objects.bulk_create(specialties)

        clinic_data = {
            "location": "Test Street",
            "longitude": 44.2,
            "latitude": 32.1,
            "phone": "011 223 3333",
        }
        Clinic.objects.create(doctor=self.doctor_with_clinic, **clinic_data)

        self.patient = User.objects.create_user(
            phone="0922334455",
            first_name="patient",
            last_name="patient",
            is_verified_phone=True,
            password=self.password,
            role="patient",
        )

        self.data = {
            "location": "Test Street",
            "longitude": 39.1,
            "latitude": 55.5,
            "phone": "011 224 4531",
        }
        self.update_data = {
            "location": "Test Update Street",
            "longitude": 66.1,
            "latitude": 32.5,
            "phone": "011 224 4533",
        }

    def test_successful_clinic_creation(self):
        self.client.force_authenticate(self.user_doctor)
        response = self.client.post(self.create_path, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("location", str(response.data))
        self.assertIn("longitude", str(response.data))
        self.assertIn("latitude", str(response.data))
        self.assertIn("phone", str(response.data))
        exists = Clinic.objects.filter(
            location=self.data["location"],
            longitude=self.data["longitude"],
            latitude=self.data["latitude"],
            phone=self.data["phone"],
        ).exists()
        self.assertTrue(exists)

    def test_successful_clinic_retrieve(self):
        self.client.force_authenticate(self.user_doctor_clinic)
        response = self.client.get(self.retrieve_update_path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("location", str(response.data))
        self.assertIn("longitude", str(response.data))
        self.assertIn("latitude", str(response.data))
        self.assertIn("phone", str(response.data))

    def test_successful_clinic_update(self):
        self.client.force_authenticate(self.user_doctor_clinic)
        response = self.client.put(
            self.retrieve_update_path,
            self.update_data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("location", str(response.data))
        self.assertIn("longitude", str(response.data))
        self.assertIn("latitude", str(response.data))
        self.assertIn("phone", str(response.data))
        exists = Clinic.objects.filter(
            location=self.update_data["location"],
            longitude=self.update_data["longitude"],
            latitude=self.update_data["latitude"],
            phone=self.update_data["phone"],
        ).exists()
        self.assertTrue(exists)

    def test_creation_fails_if_user_has_no_doctor_profile(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.create_path, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("الرجاء إنشاء حساب طبيب أولاً.", str(response.data))

    def test_retrieve_fails_if_user_has_no_doctor_profile(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.retrieve_update_path)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("الرجاء إنشاء حساب طبيب أولاً.", str(response.data))

    def test_update_fails_if_user_has_no_doctor_profile(self):
        self.client.force_authenticate(self.user)
        response = self.client.put(
            self.retrieve_update_path,
            self.update_data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("الرجاء إنشاء حساب طبيب أولاً.", str(response.data))

    def test_creation_fails_if_doctor_already_has_clinic(self):
        self.client.force_authenticate(self.user_doctor_clinic)
        response = self.client.post(self.create_path, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("لديك عيادة بالفعل.", str(response.data))

    def test_creation_fails_if_user_role_is_not_doctor(self):
        self.client.force_authenticate(self.patient)
        response = self.client.post(self.create_path, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("ليس لديك الدور المطلوب.", str(response.data))

    def test_retrieve_fails_if_user_role_is_not_doctor(self):
        self.client.force_authenticate(self.patient)
        response = self.client.get(self.retrieve_update_path)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("ليس لديك الدور المطلوب.", str(response.data))

    def test_update_fails_if_user_role_is_not_doctor(self):
        self.client.force_authenticate(self.patient)
        response = self.client.put(
            self.retrieve_update_path,
            self.update_data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("ليس لديك الدور المطلوب.", str(response.data))

    def test_creation_fails_if_unauthenticated_user_try_to_access(self):
        response = self.client.post(self.create_path, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_fails_if_unauthenticated_user_try_to_access(self):
        response = self.client.get(self.retrieve_update_path)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_fails_if_unauthenticated_user_try_to_access(self):
        response = self.client.put(
            self.retrieve_update_path,
            self.update_data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
