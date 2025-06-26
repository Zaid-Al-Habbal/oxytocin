from django.urls import reverse

from datetime import datetime, timedelta, date, time
from django.utils import timezone
from common.utils import generate_test_pdf

from rest_framework.test import APITestCase
from rest_framework import status

from users.models import CustomUser as User
from clinics.models import Clinic  
from assistants.models import Assistant
from doctors.models import Doctor, Specialty, DoctorSpecialty
from schedules.models import ClinicSchedule, AvailableHour
from patients.models import Patient

class AppointmentBaseTest(APITestCase):
    def setUp(self):
        self.password = "abcX123#"

        self.user_doctor_clinic = User.objects.create_user(
            first_name="doctor",
            last_name="clinic",
            phone="0934567891",
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
        
        self.main_specialty1 = Specialty.objects.create(
            name_en="Test1",
            name_ar="تجريبي1",
        )
        self.subspecialty1 = Specialty.objects.create(
            name_en="Test2",
            name_ar="تجريبي2",
            parent=self.main_specialty1,
        )
        specialties = [
            DoctorSpecialty(
                doctor=self.doctor_with_clinic,
                specialty=self.main_specialty1,
                university="Damascus",
            ),
            DoctorSpecialty(
                doctor=self.doctor_with_clinic,
                specialty=self.subspecialty1,
                university="Tokyo",
            ),
        ]
        DoctorSpecialty.objects.bulk_create(specialties)
        
        clinic_data = {
            "location": "Test Street",
            "longitude": 44.2,
            "latitude": 32.1,
            "phone": "011 223 3333",
        }
        self.clinic =  Clinic.objects.create(doctor=self.doctor_with_clinic, **clinic_data)

        self.assistantUser = User.objects.create_user(
            first_name="user",
            last_name="assistant",
            phone="0999888777",
            is_verified_phone=True,
            password=self.password,
            role=User.Role.ASSISTANT,
        )
        
        self.assistant = Assistant.objects.create(
            user=self.assistantUser,
            education="bla bla bla",
            start_work_date="2020-2-2",
            clinic=self.clinic
        )

        self.patient_user = User.objects.create_user(
            phone="0999111122",
            password=self.password,
            first_name="Patient",
            last_name="User",
            role="patient",
            is_verified_phone=True,
            gender="male",
            birth_date="1995-05-01"
        )

        self.patient = Patient.objects.create(
            user=self.patient_user,
            location="Damascus",
            longitude=36.29,
            latitude=33.51,
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
        
        self.weekday_schedule = ClinicSchedule.objects.get(day_name='sunday')
        AvailableHour.objects.bulk_create([
            AvailableHour(schedule=self.weekday_schedule, start_hour=time(8, 0), end_hour=time(12, 0)),
            AvailableHour(schedule=self.weekday_schedule, start_hour=time(14, 0), end_hour=time(18, 0)),
        ])
        
        self.special_date = timezone.now().date() + timedelta(days=(1+ 15 - (timezone.now().weekday() + 2) % 7 or 7))
        
        self.special_schedule = ClinicSchedule.objects.create(clinic=self.clinic, special_date=self.special_date, is_available=True)
        AvailableHour.objects.bulk_create([
            AvailableHour(schedule=self.special_schedule, start_hour=time(10, 0), end_hour=time(12, 0)),
            AvailableHour(schedule=self.special_schedule, start_hour=time(16, 0), end_hour=time(18, 0)),
        ])
        
        
        