from datetime import timedelta
from django.utils import timezone
from rest_framework.test import APITestCase
from django.contrib.gis.geos import Point
from appointments.models import Appointment
from clinics.models import Clinic
from common.utils import generate_test_pdf
from doctors.models import Doctor, DoctorSpecialty, Specialty
from users.models import CustomUser as User
from patients.models import Patient
from assistants.models import Assistant


class EvaluationBaseTestCase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.patient_user = User.objects.create_user(
            phone="0999111122",
            password="abcX123!",
            first_name="Yami",
            last_name="Sukehiro",
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
        cls.doctor_user = User.objects.create_user(
            phone="0999111123",
            password="abcX123!",
            first_name="Mereoleona",
            last_name="Vermillion",
            role=User.Role.DOCTOR.value,
            is_verified_phone=True,
            gender="female",
            birth_date="1995-05-01",
        )
        cls.doctor = Doctor.objects.create(
            user=cls.doctor_user,
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
            doctor=cls.doctor,
            specialty=cls.main_specialty,
            university="Damascus",
        )
        cls.clinic = Clinic.objects.create(
            doctor=cls.doctor,
            address="Test Street",
            location=Point(44.2, 32.1, srid=4326),
            phone="011 223 3333",
        )
        cls.in_consultation_appointment = Appointment.objects.create(
            patient=cls.patient_user,
            clinic=cls.clinic,
            visit_date=timezone.now().date(),
            visit_time=timezone.now().time(),
            status=Appointment.Status.IN_CONSULTATION.value,
        )
        cls.completed_appointment = Appointment.objects.create(
            patient=cls.patient_user,
            clinic=cls.clinic,
            visit_date=timezone.now().date(),
            visit_time=timezone.now().time(),
            status=Appointment.Status.COMPLETED.value,
        )
        cls.assistant_user = User.objects.create_user(
            phone="0999111129",
            password="abcX123!",
            first_name="Charmy",
            last_name="Pappitson",
            role=User.Role.ASSISTANT.value,
            is_verified_phone=True,
            gender="female",
            birth_date="1995-05-01",
        )
        Assistant.objects.create(
            user=cls.assistant_user,
            clinic=cls.clinic,
            education="Test",
            start_work_date=timezone.now().date() - timedelta(days=20),
        )
