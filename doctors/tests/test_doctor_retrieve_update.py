from django.urls import reverse
from django.utils import timezone

from datetime import timedelta
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import CustomUser as User
from clinics.models import Clinic

from doctors.models import Doctor, Specialty, DoctorSpecialty

from common.utils import generate_test_pdf


class DoctorRetrieveUpdateTests(APITestCase):
    def setUp(self):
        self.path = reverse("doctor-retrieve-update")
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
            "user": {
                "first_name": "John",
                "last_name": "Doe",
                "gender": "male",
                "birth_date": "1990-02-04",
            },
            "about": "Hello, I'm test doctor",
            "education": "IDK",
            "start_work_date": "2007-05-12",
            "specialties": [
                {
                    "specialty": specialty1.name,
                    "university": "Damascus",
                },
                {
                    "specialty": specialty2.name,
                    "university": "Tokyo",
                },
            ],
        }

    def test_successful_doctor_update(self):
        self.client.force_authenticate(self.user_doctor_clinic)
        response = self.client.put(self.path, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("user", str(response.data))
        self.assertIn("about", str(response.data))
        self.assertIn("education", str(response.data))
        self.assertIn("start_work_date", str(response.data))
        self.assertIn("status", str(response.data))
        self.assertIn("specialties", str(response.data))
        doctor = Doctor.objects.filter(pk=self.doctor_with_clinic.pk).get()
        self.assertEqual(doctor.user.first_name, self.data["user"]["first_name"])
        self.assertEqual(doctor.user.last_name, self.data["user"]["last_name"])
        self.assertEqual(doctor.user.gender, self.data["user"]["gender"])
        self.assertEqual(
            doctor.user.birth_date,
            timezone.datetime.strptime(
                self.data["user"]["birth_date"], "%Y-%m-%d"
            ).date(),
        )
        self.assertEqual(doctor.about, self.data["about"])
        self.assertEqual(doctor.education, self.data["education"])
        self.assertEqual(
            doctor.start_work_date,
            timezone.datetime.strptime(self.data["start_work_date"], "%Y-%m-%d").date(),
        )
        self.assertEqual(doctor.specialties.count(), len(self.data["specialties"]))
        for specialty_obj in self.data["specialties"]:
            self.assertTrue(
                doctor.doctor_specialties.filter(
                    specialty__name=specialty_obj["specialty"],
                    university=specialty_obj["university"],
                ).exists()
            )

    def test_successful_doctor_retrieve(self):
        self.client.force_authenticate(self.user_doctor_clinic)
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("user", str(response.data))
        self.assertIn("about", str(response.data))
        self.assertIn("education", str(response.data))
        self.assertIn("start_work_date", str(response.data))
        self.assertIn("specialties", str(response.data))

    def test_update_fails_if_user_has_no_doctor_profile(self):
        self.client.force_authenticate(self.user)
        response = self.client.put(self.path, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("الرجاء إنشاء حساب طبيب أولاً.", str(response.data))

    def test_retrieve_fails_if_user_has_no_doctor_profile(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("الرجاء إنشاء حساب طبيب أولاً.", str(response.data))

    def test_update_fails_if_doctor_has_no_clinic(self):
        self.client.force_authenticate(self.user_doctor)
        response = self.client.put(self.path, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("الرجاء إنشاء عيادة أولاً.", str(response.data))

    def test_retrieve_fails_if_doctor_has_no_clinic(self):
        self.client.force_authenticate(self.user_doctor)
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("الرجاء إنشاء عيادة أولاً.", str(response.data))

    def test_update_fails_if_user_role_is_not_doctor(self):
        self.client.force_authenticate(self.patient)
        response = self.client.put(self.path, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("ليس لديك الدور المطلوب.", str(response.data))

    def test_retrieve_fails_if_user_role_is_not_doctor(self):
        self.client.force_authenticate(self.patient)
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("ليس لديك الدور المطلوب.", str(response.data))

    def test_update_fails_if_unauthenticated_user_try_to_access(self):
        response = self.client.put(self.path, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_fails_if_unauthenticated_user_try_to_access(self):
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
