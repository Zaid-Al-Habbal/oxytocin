from django.urls import reverse
from django.utils import timezone

from datetime import timedelta
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import CustomUser as User

from doctors.models import Doctor, Specialty


class DoctorCreateTests(APITestCase):
    def setUp(self):
        self.path = reverse("doctor-create")
        self.password = "abcX123#"

        self.user = User.objects.create_user(
            first_name="verified",
            last_name="doctor",
            phone="0921341239",
            is_verified_phone=True,
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

        self.data = {
            "user": {
                "gender": "male",
                "birth_date": "1999-09-19",
            },
            "about": "A test about",
            "education": "about education",
            "start_work_date": timezone.now().date() - timedelta(days=30),
            "main_specialty": {
                "specialty_id": self.main_specialty1.pk,
                "university": "London",
            },
            "subspecialties": [
                {
                    "specialty_id": self.subspecialty1.pk,
                    "university": "Damascus",
                },
                {
                    "specialty_id": self.subspecialty2.pk,
                    "university": "Tokyo",
                },
            ],
        }

    def test_successful_doctor_creation(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.path, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Doctor.objects.filter(user=self.user).exists())
        self.assertIn("user", str(response.data))
        self.assertIn("gender", str(response.data))
        self.assertIn("birth_date", str(response.data))
        self.assertIn("about", str(response.data))
        self.assertIn("education", str(response.data))
        self.assertIn("start_work_date", str(response.data))
        self.assertIn("status", str(response.data))
        self.assertIn("main_specialty", str(response.data))
        self.assertIn("subspecialties", str(response.data))
        self.assertIn("university", str(response.data))
        self.assertIn("created_at", str(response.data))
        self.assertIn("updated_at", str(response.data))

    def test_fails_if_doctor_already_exists(self):
        data = self.data.copy()
        data.pop("user")
        data.pop("main_specialty")
        data.pop("subspecialties")
        Doctor.objects.create(user=self.user, **data)

        self.client.force_authenticate(self.user)
        response = self.client.post(self.path, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("لديك حساب طبيب بالفعل.", str(response.data))

    def test_fails_if_phone_is_not_verified(self):
        self.user.is_verified_phone = False
        self.user.save()
        self.user.refresh_from_db()
        self.client.force_authenticate(self.user)
        response = self.client.post(self.path, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("لم يتم التحقق من رقم الهاتف.", str(response.data))

    def test_fails_if_user_role_is_not_doctor(self):
        self.client.force_authenticate(self.patient)
        response = self.client.post(self.path, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("ليس لديك الدور المطلوب.", str(response.data))

    def test_fails_if_unauthenticated_user_try_to_access(self):
        response = self.client.post(self.path, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_fails_when_subspecialties_exceed_available_for_main_specialty(self):
        self.client.force_authenticate(self.user)
        data = self.data.copy()
        new_subspecialty = {
            "specialty_id": self.subspecialty3.pk,
            "university": "New York",
        }
        data["subspecialties"].append(new_subspecialty)
        response = self.client.post(self.path, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "لا يمكنك توفير تخصصات فرعية أكثر من تلك المتوفرة للتخصص الرئيسي.",
            str(response.data),
        )

    def test_fails_on_duplicate_subspecialties(self):
        self.client.force_authenticate(self.user)
        data = self.data.copy()
        data["subspecialties"][1] = {
            "specialty_id": self.subspecialty1.pk,
            "university": "Aleppo",
        }
        response = self.client.post(self.path, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("التكرار غير مسموح به.", str(response.data))

    def test_fails_when_one_of_subspecialties_not_under_main_specialty(self):
        self.client.force_authenticate(self.user)
        data = self.data.copy()
        data["subspecialties"][1] = {
            "specialty_id": self.subspecialty3.pk,
            "university": "Aleppo",
        }
        response = self.client.post(self.path, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("ليس فرعاً من التخصص الرئيسي.", str(response.data))

    def test_rejects_subspecialty_as_main_specialty(self):
        self.client.force_authenticate(self.user)
        data = self.data.copy()
        data["main_specialty"] = {
            "specialty_id": self.subspecialty1.pk,
            "university": "Aleppo",
        }
        response = self.client.post(self.path, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("لا يمكن أن يكون التخصص الرئيسي تخصصاً فرعياً.", str(response.data))

    def test_rejects_main_specialty_as_subspecialty(self):
        self.client.force_authenticate(self.user)
        data = self.data.copy()
        data["subspecialties"][1] = {
            "specialty_id": self.main_specialty2.pk,
            "university": "Aleppo",
        }
        response = self.client.post(self.path, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("ليس فرعاً من التخصص الرئيسي", str(response.data))
