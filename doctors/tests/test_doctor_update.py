from django.urls import reverse
from django.utils import timezone
from django.contrib.gis.geos import Point

from datetime import timedelta
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import CustomUser as User
from clinics.models import Clinic

from doctors.models import Doctor, Specialty, DoctorSpecialty

from common.utils import generate_test_pdf


class DoctorUpdateTests(APITestCase):
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
        )
        self.subspecialty1.main_specialties.add(self.main_specialty1)

        self.subspecialty2 = Specialty.objects.create(
            name_en="Test3",
            name_ar="تجريبي3",
        )
        self.subspecialty2.main_specialties.add(self.main_specialty1)

        self.main_specialty2 = Specialty.objects.create(
            name_en="Test4",
            name_ar="تجريبي4",
        )

        self.subspecialty3 = Specialty.objects.create(
            name_en="Test5",
            name_ar="تجريبي5",
        )
        self.subspecialty3.main_specialties.add(self.main_specialty2)
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
            "address": "Test Street",
            "location": Point(44.2, 32.1, srid=4326),
            "phone": "011 223 3333",
        }
        Clinic.objects.create(doctor=self.doctor, **clinic_data)

        self.data = {
            "user": {
                "first_name": "John",
                "last_name": "Doe",
                "gender": "male",
                "birth_date": "1990-02-04",
            },
            "about": "Hello, I'm good doctor",
            "education": "IDK",
            "start_work_date": "2007-05-12",
            "subspecialties": [
                {
                    "specialty_id": self.subspecialty1.pk,
                    "university": "Tokyo",
                },
                {
                    "specialty_id": self.subspecialty2.pk,
                    "university": "Tokyo",
                },
            ],
        }

    def test_successful_doctor_update(self):
        self.client.force_authenticate(self.user)
        response = self.client.put(self.path, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("user", str(response.data))
        self.assertIn("about", str(response.data))
        self.assertIn("education", str(response.data))
        self.assertIn("start_work_date", str(response.data))
        self.assertIn("status", str(response.data))
        self.assertIn("main_specialty", str(response.data))
        self.assertIn("subspecialties", str(response.data))
        self.doctor.refresh_from_db()
        self.assertEqual(self.doctor.user.first_name, self.data["user"]["first_name"])
        self.assertEqual(self.doctor.user.last_name, self.data["user"]["last_name"])
        self.assertEqual(self.doctor.user.gender, self.data["user"]["gender"])
        self.assertEqual(
            self.doctor.user.birth_date,
            timezone.datetime.strptime(
                self.data["user"]["birth_date"], "%Y-%m-%d"
            ).date(),
        )
        self.assertEqual(self.doctor.about, self.data["about"])
        self.assertEqual(self.doctor.education, self.data["education"])
        self.assertEqual(
            self.doctor.start_work_date,
            timezone.datetime.strptime(self.data["start_work_date"], "%Y-%m-%d").date(),
        )
        self.assertEqual(
            self.doctor.specialties.subspecialties_only().count(),
            len(self.data["subspecialties"]),
        )
        for subspecialty_obj in self.data["subspecialties"]:
            self.assertTrue(
                self.doctor.doctor_specialties.filter(
                    specialty__id=subspecialty_obj["specialty_id"],
                    university=subspecialty_obj["university"],
                ).exists()
            )

    def test_update_fails_when_subspecialties_exceed_available_for_main_specialty(self):
        self.client.force_authenticate(self.user)
        data = self.data.copy()
        new_subspecialty = {
            "specialty_id": self.subspecialty2.pk,
            "university": "New York",
        }
        data["subspecialties"].append(new_subspecialty)
        response = self.client.put(self.path, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "لا يمكنك توفير تخصصات فرعية أكثر من تلك المتوفرة للتخصص الرئيسي.",
            str(response.data),
        )

    def test_update_fails_on_duplicate_subspecialties(self):
        self.client.force_authenticate(self.user)
        data = self.data.copy()
        data["subspecialties"][1] = {
            "specialty_id": self.subspecialty1.pk,
            "university": "Aleppo",
        }
        response = self.client.put(self.path, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("التكرار غير مسموح به.", str(response.data))

    def test_update_fails_when_one_of_subspecialties_not_under_main_specialty(self):
        self.client.force_authenticate(self.user)
        data = self.data.copy()
        data["subspecialties"][1] = {
            "specialty_id": self.subspecialty3.pk,
            "university": "Aleppo",
        }
        response = self.client.put(self.path, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("ليس فرعاً من التخصص الرئيسي.", str(response.data))

    def test_update_rejects_main_specialty_as_subspecialty(self):
        self.client.force_authenticate(self.user)
        data = self.data.copy()
        data["subspecialties"][1] = {
            "specialty_id": self.main_specialty2.pk,
            "university": "Aleppo",
        }
        response = self.client.put(self.path, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("ليس تخصصاً فرعياً.", str(response.data))
