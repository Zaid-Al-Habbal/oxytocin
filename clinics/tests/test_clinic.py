from django.urls import reverse
from django.utils import timezone

from datetime import timedelta
from rest_framework import status
from rest_framework.test import APITestCase

from common.utils import generate_test_pdf

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

        doctor_data = {
            "about": "About Test",
            "education": "Test",
            "certificate": generate_test_pdf(),
            "start_work_date": timezone.now().date() - timedelta(days=30),
            "status": Doctor.Status.APPROVED,
        }

        self.doctor = Doctor.objects.create(
            user=self.user,
            **doctor_data,
        )

        main_specialty1 = Specialty.objects.create(name_en="Test1", name_ar="تجريبي1")
        subspecialty1 = Specialty.objects.create(
            name_en="Test2",
            name_ar="تجريبي2",
        )
        subspecialty1.main_specialties.add(main_specialty1)
        specialties = [
            DoctorSpecialty(
                doctor=self.doctor,
                specialty=main_specialty1,
                university="Damascus",
            ),
            DoctorSpecialty(
                doctor=self.doctor,
                specialty=subspecialty1,
                university="Tokyo",
            ),
        ]
        DoctorSpecialty.objects.bulk_create(specialties)

        clinic_data = {
            "location": "Test Street",
            "longitude": 44.2,
            "latitude": 32.1,
            "phone": "011 223 3333",
        }
        self.clinic = Clinic.objects.create(doctor=self.doctor, **clinic_data)

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
        self.clinic.delete()
        self.user.refresh_from_db()
        self.client.force_authenticate(self.user)
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
        self.client.force_authenticate(self.user)
        response = self.client.get(self.retrieve_update_path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("location", str(response.data))
        self.assertIn("longitude", str(response.data))
        self.assertIn("latitude", str(response.data))
        self.assertIn("phone", str(response.data))

    def test_successful_clinic_update(self):
        self.client.force_authenticate(self.user)
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

    def test_creation_view_rejects_users_without_doctor_profile(self):
        self.doctor.delete()
        self.user.refresh_from_db()
        self.client.force_authenticate(self.user)
        response = self.client.post(self.create_path, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("الرجاء إنشاء حساب طبيب أولاً.", str(response.data))

    def test_retrieve_update_view_rejects_users_without_doctor_profile(self):
        self.doctor.delete()
        self.user.refresh_from_db()
        self.client.force_authenticate(self.user)
        response = self.client.get(self.retrieve_update_path)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("الرجاء إنشاء حساب طبيب أولاً.", str(response.data))

    def test_creation_view_rejects_users_without_certificate(self):
        self.doctor.certificate = None
        self.doctor.save()
        self.user.refresh_from_db()
        self.client.force_authenticate(self.user)
        response = self.client.post(self.create_path, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("يرجى رفع الشهادة اولاً.", str(response.data))

    def test_retrieve_update_view_rejects_users_without_certificate(self):
        self.doctor.certificate = None
        self.doctor.save()
        self.user.refresh_from_db()
        self.client.force_authenticate(self.user)
        response = self.client.get(self.retrieve_update_path)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("يرجى رفع الشهادة اولاً.", str(response.data))

    def test_creation_fails_if_doctor_already_has_clinic(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.create_path, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("لديك عيادة بالفعل.", str(response.data))

    def test_creation_view_rejects_users_with_non_doctor_role(self):
        self.client.force_authenticate(self.patient)
        response = self.client.post(self.create_path, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("ليس لديك الدور المطلوب.", str(response.data))

    def test_retrieve_update_view_rejects_users_with_non_doctor_role(self):
        self.client.force_authenticate(self.patient)
        response = self.client.get(self.retrieve_update_path)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("ليس لديك الدور المطلوب.", str(response.data))

    def test_creation_view_rejects_unauthenticated_users(self):
        response = self.client.post(self.create_path, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_update_view_rejects_unauthenticated_users(self):
        response = self.client.get(self.retrieve_update_path)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
