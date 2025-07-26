from datetime import timedelta
from django.utils import timezone
from rest_framework.test import APITestCase
from django.contrib.gis.geos import Point
from clinics.models import Clinic
from common.utils import generate_test_pdf
from doctors.models import Doctor, DoctorSpecialty, Specialty
from favorites.models import Favorite
from users.models import CustomUser as User
from patients.models import Patient


class FavoriteBaseTestCase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.patient_user = User.objects.create_user(
            phone="0999111122",
            password="abcX123!",
            first_name="Xiaoshi",
            last_name="Cheng",
            role=User.Role.PATIENT.value,
            is_verified_phone=True,
            gender="male",
            birth_date="1995-05-01",
        )
        cls.patient = Patient.objects.create(
            user=cls.patient_user,
            address="Damascus",
            location=Point(36.29, 33.51, srid=4326),
            job="Engineer",
            blood_type="A+",
            medical_history="",
            surgical_history="",
            allergies="",
            medicines="",
            is_smoker=False,
            is_drinker=False,
            is_married=False,
        )
        cls.favorite_doctor_user = User.objects.create_user(
            phone="0999111123",
            password="abcX123!",
            first_name="Guang",
            last_name="Lu",
            role=User.Role.DOCTOR.value,
            is_verified_phone=True,
            gender="male",
            birth_date="1995-05-01",
        )
        cls.favorite_doctor = Doctor.objects.create(
            user=cls.favorite_doctor_user,
            about="About Test",
            education="Test",
            certificate=generate_test_pdf(),
            start_work_date=timezone.now().date() - timedelta(days=30),
            status=Doctor.Status.APPROVED.value,
        )
        cls.main_specialty = Specialty.objects.create(
            name_en="Test1",
            name_ar="تجريبي1",
        )
        DoctorSpecialty.objects.create(
            doctor=cls.favorite_doctor,
            specialty=cls.main_specialty,
            university="Damascus",
        )
        Clinic.objects.create(
            doctor=cls.favorite_doctor,
            address="Test Street",
            location=Point(44.2, 32.1, srid=4326),
            phone="011 223 3333",
        )
        cls.favorite = Favorite.objects.create(
            patient=cls.patient,
            doctor=cls.favorite_doctor,
        )
