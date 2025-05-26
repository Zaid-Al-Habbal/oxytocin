from django.urls import reverse
from django.utils import timezone

from datetime import timedelta
from rest_framework import status
from rest_framework.test import APITestCase

from common.utils import generate_test_image, generate_test_pdf

from users.models import CustomUser as User
from doctors.models import Doctor, Specialty, DoctorSpecialty

from clinics.models import Clinic, ClinicImage


class ClinicImageTests(APITestCase):

    def setUp(self):
        self.path = reverse("clinic-images")
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
        self.clinic = Clinic.objects.create(
            doctor=self.doctor_with_clinic, **clinic_data
        )

        self.patient = User.objects.create_user(
            phone="0922334455",
            first_name="patient",
            last_name="patient",
            is_verified_phone=True,
            password=self.password,
            role="patient",
        )

    def create_clinic_image(self, clinic):
        clinic_image = ClinicImage.objects.create(
            clinic=clinic, image=generate_test_image()
        )
        return clinic_image

    def test_successful_image_creation(self):
        self.client.force_authenticate(self.user_doctor_clinic)
        data = {"images": [generate_test_image(), generate_test_image()]}
        response = self.client.post(self.path, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("clinic_images", str(response.data))
        self.assertEqual(len(response.data["clinic_images"]), len(data["images"]))
        self.assertIn("id", str(response.data))
        self.assertIn("image", str(response.data))
        self.assertIn("created_at", str(response.data))
        self.assertIn("updated_at", str(response.data))

    def test_successful_image_update(self):
        self.client.force_authenticate(self.user_doctor_clinic)
        clinic_image = self.create_clinic_image(self.clinic)
        data = {
            "clinic_images[0]id": clinic_image.pk,
            "clinic_images[0]image": generate_test_image(color=(0, 0, 255)),
        }
        response = self.client.put(self.path, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("clinic_images", str(response.data))
        self.assertEqual(len(response.data["clinic_images"]), len(data) / 2)
        self.assertIn("id", str(response.data))
        self.assertIn("image", str(response.data))
        self.assertIn("created_at", str(response.data))
        self.assertIn("updated_at", str(response.data))
        updated_clinic_image = ClinicImage.objects.filter(pk=clinic_image.pk).get()
        self.assertNotEqual(updated_clinic_image.image, clinic_image.image)
        self.assertGreater(updated_clinic_image.updated_at, clinic_image.updated_at)

    def test_successful_image_deletion(self):
        self.client.force_authenticate(self.user_doctor_clinic)
        clinic_image = self.create_clinic_image(self.clinic)
        data = {
            "clinic_images": [clinic_image.pk],
        }
        response = self.client.delete(self.path, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        exists = ClinicImage.objects.filter(pk=clinic_image.pk).exists()
        self.assertFalse(exists)

    def test_creation_fails_if_number_of_uploaded_images_exceeds_the_limit(self):
        self.client.force_authenticate(self.user_doctor_clinic)
        self.create_clinic_image(self.clinic)
        data = {
            "images": [
                generate_test_image(),
                generate_test_image(),
                generate_test_image(),
                generate_test_image(),
                generate_test_image(),
                generate_test_image(),
                generate_test_image(),
                generate_test_image(),
            ]
        }
        response = self.client.post(self.path, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("يمكنك رفع مايصل الى 8 صور كحد أقصى.", str(response.data))

    def test_update_fails_on_unowned_images(self):
        self.client.force_authenticate(self.user_doctor_clinic)
        clinic_data = {
            "location": "Test Street 3",
            "longitude": 74.2,
            "latitude": 92.1,
            "phone": "011 223 4444",
        }
        clinic = Clinic.objects.create(doctor=self.doctor_without_clinic, **clinic_data)
        clinic_image = self.create_clinic_image(clinic)
        data = {
            "clinic_images[0]id": clinic_image.pk,
            "clinic_images[0]image": generate_test_image(),
        }
        response = self.client.put(self.path, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("العنصر غير موجود", str(response.data))

    def test_update_fails_on_nonexistent_images(self):
        self.client.force_authenticate(self.user_doctor_clinic)
        data = {
            "clinic_images[0]id": 999999,
            "clinic_images[0]image": generate_test_image(),
        }
        response = self.client.put(self.path, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("العنصر غير موجود", str(response.data))

    def test_deletion_fails_on_delete_unowned_images(self):
        self.client.force_authenticate(self.user_doctor_clinic)
        clinic_data = {
            "location": "Test Street 3",
            "longitude": 74.2,
            "latitude": 92.1,
            "phone": "011 223 4444",
        }
        clinic = Clinic.objects.create(doctor=self.doctor_without_clinic, **clinic_data)
        clinic_image = self.create_clinic_image(clinic)
        data = {"clinic_images": [clinic_image.pk]}
        response = self.client.delete(self.path, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("العنصر غير موجود", str(response.data))

    def test_deletion_fails_on_delete_nonexistent_images(self):
        self.client.force_authenticate(self.user_doctor_clinic)
        data = {"clinic_images": [99]}
        response = self.client.delete(self.path, data, format="json")
        self.assertTrue(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("العنصر غير موجود", str(response.data))

    def test_deletion_fails_on_duplicate_pks(self):
        self.client.force_authenticate(self.user_doctor_clinic)
        clinic_image = self.create_clinic_image(self.clinic)
        data = {"clinic_images": [clinic_image.pk, clinic_image.pk]}
        response = self.client.delete(self.path, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("التكرار غير مسموح به.", str(response.data))

    def test_creation_fails_if_user_role_is_not_doctor(self):
        self.client.force_authenticate(self.patient)
        data = {"images": [generate_test_image(), generate_test_image()]}
        response = self.client.post(self.path, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("ليس لديك الدور المطلوب.", str(response.data))

    def test_update_fails_if_user_role_is_not_doctor(self):
        self.client.force_authenticate(self.patient)
        clinic_image = self.create_clinic_image(self.clinic)
        data = {
            "clinic_images[0]id": clinic_image.pk,
            "clinic_images[0]image": generate_test_image(color=(0, 0, 255)),
        }
        response = self.client.put(self.path, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("ليس لديك الدور المطلوب.", str(response.data))

    def test_deletion_fails_if_user_role_is_not_doctor(self):
        self.client.force_authenticate(self.patient)
        clinic_image = self.create_clinic_image(self.clinic)
        data = {
            "clinic_images": [clinic_image.pk],
        }
        response = self.client.delete(self.path, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("ليس لديك الدور المطلوب.", str(response.data))

    def test_creation_fails_on_unauthenticated_user(self):
        data = {"images": [generate_test_image(), generate_test_image()]}
        response = self.client.post(self.path, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_fails_on_unauthenticated_user(self):
        clinic_image = self.create_clinic_image(self.clinic)
        data = {
            "clinic_images[0]id": clinic_image.pk,
            "clinic_images[0]image": generate_test_image(color=(0, 0, 255)),
        }
        response = self.client.put(self.path, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_deletion_fails_on_unauthenticated_user(self):
        clinic_image = self.create_clinic_image(self.clinic)
        data = {
            "clinic_images": [clinic_image.pk],
        }
        response = self.client.delete(self.path, data, format="json")
        response = self.client.put(self.path, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
