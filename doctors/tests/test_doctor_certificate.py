from django.urls import reverse
from django.utils import timezone

from datetime import timedelta
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import CustomUser as User

from doctors.models import Doctor

from common.utils import generate_test_pdf


class DoctorCertificateTests(APITestCase):
    def setUp(self):
        self.path = reverse("doctor-certificate")
        self.password = "abcX123#"
        self.user = User.objects.create_user(
            first_name="verified",
            last_name="doctor",
            phone="0921341239",
            is_verified_phone=True,
            password=self.password,
            role=User.Role.DOCTOR,
        )
        doctor_data = {
            "about": "About Test",
            "education": "Test",
            "start_work_date": timezone.now().date() - timedelta(days=30),
            "status": Doctor.Status.APPROVED,
        }
        self.doctor = Doctor.objects.create(user=self.user, **doctor_data)
        self.patient = User.objects.create_user(
            first_name="patient",
            last_name="patient",
            phone="0921341241",
            is_verified_phone=True,
            password=self.password,
            role=User.Role.PATIENT,
        )

        self.data = {"certificate": generate_test_pdf()}

    def test_successful_certificate_upload(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.path, self.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("تم رفع شهادة الطبيب بنجاح.", str(response.data))
        self.doctor.refresh_from_db()
        self.assertIsNotNone(self.doctor.certificate)
        self.assertNotEqual(self.doctor.certificate, "")

    def test_fails_if_user_role_is_not_doctor(self):
        self.client.force_authenticate(self.patient)
        response = self.client.post(self.path, self.data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("ليس لديك الدور المطلوب.", str(response.data))

    def test_fails_if_user_has_no_doctor_profile(self):
        self.doctor.delete()
        self.user.refresh_from_db()
        self.client.force_authenticate(self.user)
        response = self.client.post(self.path, self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("الرجاء إنشاء حساب طبيب أولاً.", str(response.data))

    def test_fails_when_certificate_already_exists(self):
        self.doctor.certificate = generate_test_pdf()
        self.doctor.save()
        self.user.refresh_from_db()
        self.client.force_authenticate(self.user)
        response = self.client.post(self.path, self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("لقد تم بالفعل رفع شهادة لملف هذا الطبيب.", str(response.data))
