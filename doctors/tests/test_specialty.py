from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from doctors.models import Specialty


class SpecialtyTests(APITestCase):

    def setUp(self):
        self.path = reverse("specialty-list")

        self.main_specialties = [
            Specialty.objects.create(
                name_en="Test1",
                name_ar="تجريبي1",
            ),
            Specialty.objects.create(
                name_en="Test4",
                name_ar="تجريبي4",
            ),
        ]
        self.subspecialties = [
            Specialty.objects.create(
                name_en="Test2",
                name_ar="تجريبي2",
                parent=self.main_specialties[0],
            ),
            Specialty.objects.create(
                name_en="Test3",
                name_ar="تجريبي3",
                parent=self.main_specialties[0],
            ),
            Specialty.objects.create(
                name_en="Test5",
                name_ar="تجريبي5",
                parent=self.main_specialties[1],
            ),
        ]

    def test_list_specialties_success(self):
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(self.main_specialties), len(response.data))
        self.assertIn("id", str(response.data))
        self.assertIn("name_en", str(response.data))
        self.assertIn("name_ar", str(response.data))
        self.assertIn("subspecialties", str(response.data))
