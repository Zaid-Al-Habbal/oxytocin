from datetime import timedelta
from django.contrib.gis.geos import Point
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from clinics.models import Clinic
from common.utils import generate_test_pdf
from doctors.models import Doctor, DoctorSpecialty
from favorites.models import Favorite
from users.models import CustomUser as User

from .base import FavoriteBaseTestCase


class FavoriteDestroyTestCase(FavoriteBaseTestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        favorite_doctor_user_for_destroy = User.objects.create_user(
            phone="0999111124",
            password="abcX123!",
            first_name="Ling",
            last_name="Qiao",
            role=User.Role.DOCTOR.value,
            is_verified_phone=True,
            gender="female",
            birth_date="1995-05-01",
        )
        favorite_doctor_for_destroy = Doctor.objects.create(
            user=favorite_doctor_user_for_destroy,
            about="About Test",
            education="Test",
            certificate=generate_test_pdf(),
            start_work_date=timezone.now().date() - timedelta(days=30),
            status=Doctor.Status.APPROVED.value,
        )
        DoctorSpecialty.objects.create(
            doctor=favorite_doctor_for_destroy,
            specialty=cls.main_specialty,
            university="Damascus",
        )
        Clinic.objects.create(
            doctor=favorite_doctor_for_destroy,
            address="Test Street",
            location=Point(44.2, 32.1, srid=4326),
            phone="011 223 3322",
        )
        favorite = Favorite.objects.create(
            patient=cls.patient,
            doctor=favorite_doctor_for_destroy,
        )
        cls.path = reverse("favorite-destroy", kwargs={"pk": favorite.pk})

    def test_destroy_successful(self):
        self.client.force_authenticate(self.patient_user)
        response = self.client.delete(self.path)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_view_rejects_users_with_non_patient_role(self):
        path = reverse("favorite-destroy", kwargs={"pk": self.favorite.pk})
        self.client.force_authenticate(self.favorite_doctor_user)
        response = self.client.delete(path)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_view_rejects_unauthenticated_users(self):
        path = reverse("favorite-destroy", kwargs={"pk": self.favorite.pk})
        response = self.client.delete(path)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
