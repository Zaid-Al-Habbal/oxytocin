from django.urls import reverse
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile

from PIL import Image
from reportlab.pdfgen import canvas
from io import BytesIO
from datetime import timedelta
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import CustomUser as User
from clinics.models import Clinic

from .models import Doctor, Specialty, DoctorSpecialty


def generate_test_image(
    mode: str = "RGB",
    name: str = "test_image.jpg",
    size: tuple[int, int] | list[int] = (100, 100),
    color: float | tuple[float, ...] | str = (255, 0, 0),
    image_format: str = "JPEG",
    content_type: str = "image/jpeg",
):
    """
    Create a simple in-memory image file for use in Django tests.

    This utility generates an image of the specified mode, dimensions, and fill color,
    saves it into a bytes buffer in the chosen format, and wraps it in a
    `SimpleUploadedFile` to simulate an uploaded image without touching the filesystem.

    Parameters
    ----------
    mode : str, optional
        The color mode for the new image (e.g., "RGB", "RGBA", "L"), by default "RGB".
    name : str, optional
        The filename to assign to the uploaded image (default is "test_image.jpg").
    size : tuple[int, int] or list[int], optional
        The (width, height) in pixels for the generated image (default is (100, 100)).
    color : float, tuple of floats, or str, optional
        The fill color for the image background. For an RGB image, a 3-tuple of ints
        or a CSS-style string is valid (default is red `(255, 0, 0)`).
    image_format : str, optional
        The file format to use when encoding the image (e.g., "JPEG", "PNG"), default "JPEG".
    content_type : str, optional
        The MIME type to set on the `SimpleUploadedFile` (default is "image/jpeg").

    Returns
    -------
    SimpleUploadedFile
        A Django `SimpleUploadedFile` containing the generated image bytes,
        suitable for use in form or view tests that accept file uploads.

    Example
    -------
    ```python
    # Generate a 50x50 blue PNG for testing a profile picture upload:
    avatar = generate_test_image(
        mode="RGB",
        name="avatar.png",
        size=(50, 50),
        color=(0, 0, 255),
        image_format="PNG",
        content_type="image/png"
    )
    ```
    """
    image = Image.new(mode, size, color=color)
    buffer = BytesIO()
    image.save(buffer, format=image_format)
    buffer.seek(0)
    return SimpleUploadedFile(name, buffer.read(), content_type=content_type)


def generate_test_pdf(
    name: str = "test.pdf",
    text: str = "This is a test PDF file.",
):
    """
    Generates a simple in-memory PDF file with the specified text content.

    Parameters:
        name (str): The name to assign to the generated PDF file (default is "test.pdf").
        text (str): The text to be written on the PDF (default is "This is a test PDF file.").

    Returns:
        SimpleUploadedFile: A Django-compatible in-memory uploaded file object containing the PDF,
                            suitable for use in tests or file upload simulations.
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer)
    c.drawString(100, 750, text)
    c.save()
    buffer.seek(0)
    return SimpleUploadedFile(name, buffer.read(), content_type="application/pdf")


class DoctorLoginTests(APITestCase):
    def setUp(self):
        self.path = reverse("doctor-login")
        self.password = "abcX123#"

        self.verified_doctor = User.objects.create_user(
            first_name="verified",
            last_name="doctor",
            phone="0934567899",
            is_verified_phone=True,
            password=self.password,
            role=User.Role.DOCTOR,
        )

        self.unverified_doctor = User.objects.create_user(
            first_name="unverified",
            last_name="doctor",
            phone="0987654324",
            is_verified_phone=False,
            password=self.password,
            role=User.Role.DOCTOR,
        )

        self.patient = User.objects.create_user(
            first_name="patient",
            last_name="patient",
            phone="0922334455",
            is_verified_phone=True,
            password=self.password,
            role=User.Role.PATIENT,
        )

    def test_successful_if_doctor_phone_is_verified(self):
        data = {
            "phone": self.verified_doctor.phone,
            "password": self.password,
        }
        response = self.client.post(self.path, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access_token", response.data)
        self.assertIn("refresh_token", response.data)
        self.assertIn("expires_in", response.data)

    def test_fails_if_doctor_phone_is_not_verified(self):
        data = {
            "phone": self.unverified_doctor.phone,
            "password": self.password,
        }
        response = self.client.post(self.path, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("الرجاء تاكيد الرقم أولاً.", str(response.data))

    def test_fails_if_user_role_is_not_doctor(self):
        data = {
            "phone": self.patient.phone,
            "password": self.password,
        }
        response = self.client.post(self.path, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non_field_errors", response.data)
        self.assertIn("بيانات اعتماد خاطئة!", str(response.data))

    def test_login_with_wrong_password(self):
        data = {
            "phone": self.verified_doctor.phone,
            "password": "Wr0ng_Passw0rd",
        }
        response = self.client.post(self.path, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non_field_errors", response.data)
        self.assertIn("بيانات اعتماد خاطئة!", str(response.data))

    def test_login_with_non_existing_user(self):
        data = {
            "phone": "0922222222",
            "password": self.password,
        }
        response = self.client.post(self.path, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non_field_errors", response.data)
        self.assertIn("بيانات اعتماد خاطئة!", str(response.data))


class DoctorCreateTests(APITestCase):
    def setUp(self):
        self.path = reverse("doctor-create")
        self.password = "abcX123#"

        self.verified_doctor = User.objects.create_user(
            first_name="verified",
            last_name="doctor",
            phone="0921341239",
            is_verified_phone=True,
            password=self.password,
            role=User.Role.DOCTOR,
        )

        self.unverified_doctor = User.objects.create_user(
            first_name="unverified",
            last_name="doctor",
            phone="0921341240",
            is_verified_phone=False,
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

        specialty1 = Specialty.objects.create(name="Test1")
        specialty2 = Specialty.objects.create(name="Test2", parent=specialty1)

        self.data = {
            "user.gender": "male",
            "user.birth_date": "1999-09-19",
            "about": "A test about",
            "education": "about education",
            "start_work_date": timezone.now().date() - timedelta(days=30),
            "certificate": generate_test_pdf(),
            "specialties[0]specialty": specialty1.name,
            "specialties[0]university": "Test1 university",
            "specialties[1]specialty": specialty2.name,
            "specialties[1]university": "Test2 university",
        }

    def test_successful_doctor_creation(self):
        self.client.force_authenticate(self.verified_doctor)
        response = self.client.post(self.path, self.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Doctor.objects.filter(user=self.verified_doctor).exists())
        self.assertIn("user", str(response.data))
        self.assertIn("gender", str(response.data))
        self.assertIn("birth_date", str(response.data))
        self.assertIn("about", str(response.data))
        self.assertIn("education", str(response.data))
        self.assertIn("start_work_date", str(response.data))
        self.assertIn("status", str(response.data))
        self.assertIn("specialties", str(response.data))
        self.assertIn("specialty", str(response.data))
        self.assertIn("university", str(response.data))
        self.assertIn("created_at", str(response.data))
        self.assertIn("updated_at", str(response.data))

    def test_fails_if_doctor_already_exists(self):
        data = self.data.copy()
        data.pop("user.gender")
        data.pop("user.birth_date")
        data.pop("specialties[0]specialty")
        data.pop("specialties[0]university")
        data.pop("specialties[1]specialty")
        data.pop("specialties[1]university")
        Doctor.objects.create(user=self.verified_doctor, **data)

        self.client.force_authenticate(self.verified_doctor)

        self.data["certificate"] = generate_test_pdf()
        response = self.client.post(self.path, self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("لديك حساب طبيب بالفعل.", str(response.data))

    def test_fails_if_phone_is_not_verified(self):
        self.client.force_authenticate(self.unverified_doctor)
        response = self.client.post(self.path, self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("لم يتم التحقق من رقم الهاتف.", str(response.data))

    def test_fails_if_user_role_is_not_doctor(self):
        self.client.force_authenticate(self.patient)
        response = self.client.post(self.path, self.data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("ليس لديك الدور المطلوب.", str(response.data))

    def test_fails_if_unauthenticated_user_try_to_access(self):
        response = self.client.post(self.path, self.data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


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
