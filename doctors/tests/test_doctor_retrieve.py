from django.urls import reverse
from django.utils import timezone

from datetime import timedelta
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import CustomUser as User
from clinics.models import Clinic

from doctors.models import Doctor, Specialty, DoctorSpecialty

from common.utils import generate_test_pdf


class DoctorRetrieveTests(APITestCase):
    def setUp(self):
        self.path = reverse("doctor-retrieve-update")
        self.password = "abcX123#"

        self.user = User.objects.create_user(
            first_name="doctor",
            last_name="user",
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

        self.main_specialty1 = Specialty.objects.create(
            name_en="Test1",
            name_ar="تجريبي1",
        )
        self.subspecialty1 = Specialty.objects.create(
            name_en="Test2",
            name_ar="تجريبي2",
            parent=self.main_specialty1,
        )
        self.subspecialty2 = Specialty.objects.create(
            name_en="Test3",
            name_ar="تجريبي3",
            parent=self.main_specialty1,
        )
        self.main_specialty2 = Specialty.objects.create(
            name_en="Test4",
            name_ar="تجريبي4",
        )
        self.subspecialty3 = Specialty.objects.create(
            name_en="Test5",
            name_ar="تجريبي5",
            parent=self.main_specialty2,
        )
        specialties = [
            DoctorSpecialty(
                doctor=self.doctor,
                specialty=self.main_specialty1,
                university="Damascus",
            ),
            DoctorSpecialty(
                doctor=self.doctor,
                specialty=self.subspecialty1,
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

    def test_successful_doctor_retrieve(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("user", str(response.data))
        self.assertIn("about", str(response.data))
        self.assertIn("education", str(response.data))
        self.assertIn("start_work_date", str(response.data))
        self.assertIn("main_specialty", str(response.data))
        self.assertIn("subspecialties", str(response.data))

    def test_view_rejects_users_without_doctor_profile(self):
        self.doctor.delete()
        self.user.refresh_from_db()
        self.client.force_authenticate(self.user)
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("الرجاء إنشاء حساب طبيب أولاً.", str(response.data))

    def test_view_rejects_users_without_certificate(self):
        self.doctor.certificate = None
        self.doctor.save()
        self.user.refresh_from_db()
        self.client.force_authenticate(self.user)
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("يرجى رفع الشهادة اولاً.", str(response.data))

    def test_view_rejects_doctors_without_clinic(self):
        self.clinic.delete()
        self.user.refresh_from_db()
        self.client.force_authenticate(self.user)
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("الرجاء إنشاء عيادة أولاً.", str(response.data))

    def test_view_rejects_users_with_non_doctor_role(self):
        self.client.force_authenticate(self.patient)
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("ليس لديك الدور المطلوب.", str(response.data))

    def test_view_rejects_unauthenticated_users(self):
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
