from datetime import timedelta
from django.contrib.gis.geos import Point
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from clinics.models import Clinic
from common.utils import generate_test_pdf
from doctors.models import Doctor, DoctorSpecialty
from users.models import CustomUser as User

from .base import FavoriteBaseTestCase


class FavoriteListCreateTestCase(FavoriteBaseTestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.path = reverse("favorite-list-create")
        cls.unfavorite_doctor_user = User.objects.create_user(
            phone="0999111124",
            password="abcX123!",
            first_name="Ling",
            last_name="Qiao",
            role=User.Role.DOCTOR.value,
            is_verified_phone=True,
            gender="female",
            birth_date="1995-05-01",
        )
        cls.unfavorite_doctor = Doctor.objects.create(
            user=cls.unfavorite_doctor_user,
            about="About Test",
            education="Test",
            certificate=generate_test_pdf(),
            start_work_date=timezone.now().date() - timedelta(days=30),
            status=Doctor.Status.APPROVED.value,
        )
        DoctorSpecialty.objects.create(
            doctor=cls.unfavorite_doctor,
            specialty=cls.main_specialty,
            university="Damascus",
        )
        Clinic.objects.create(
            doctor=cls.unfavorite_doctor,
            address="Test Street",
            location=Point(44.2, 32.1, srid=4326),
            phone="011 223 3322",
        )

    def test_list_successful(self):
        self.client.force_authenticate(self.patient_user)
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", str(response.data))

    def test_create_successful(self):
        self.client.force_authenticate(self.patient_user)
        data = {"doctor_id": self.unfavorite_doctor.pk}
        response = self.client.post(self.path, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("doctor", str(response.data))

    def test_create_rejects_already_exists_doctor(self):
        self.client.force_authenticate(self.patient_user)
        data = {"doctor_id": self.favorite_doctor.pk}
        response = self.client.post(self.path, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("الطبيب موجود بالفعل في المفضلة", str(response.data))

    def test_view_rejects_users_with_non_patient_role(self):
        self.client.force_authenticate(self.favorite_doctor_user)
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_view_rejects_unauthenticated_users(self):
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
