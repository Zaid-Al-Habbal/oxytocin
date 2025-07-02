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
        subspecialty1 = Specialty.objects.create(
            name_en="Test2",
            name_ar="تجريبي2",
        )
        subspecialty1.main_specialties.add(self.main_specialties[0])

        subspecialty2 = Specialty.objects.create(
            name_en="Test3",
            name_ar="تجريبي3",
        )
        subspecialty2.main_specialties.add(self.main_specialties[0])

        subspecialty3 = Specialty.objects.create(
            name_en="Test5",
            name_ar="تجريبي5",
        )
        subspecialty3.main_specialties.add(self.main_specialties[1])

        self.subspecialties = [subspecialty1, subspecialty2, subspecialty3]

    def test_list_specialties_success(self):
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(self.main_specialties), len(response.data))
        self.assertIn("id", str(response.data))
        self.assertIn("name_en", str(response.data))
        self.assertIn("name_ar", str(response.data))
        self.assertIn("subspecialties", str(response.data))
