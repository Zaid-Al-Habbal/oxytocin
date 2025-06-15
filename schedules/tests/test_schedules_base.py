from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from common.utils import generate_test_pdf

from rest_framework.test import APITestCase
from rest_framework import status

from users.models import CustomUser as User
from clinics.models import Clinic  
from assistants.models import Assistant
from doctors.models import Doctor, Specialty, DoctorSpecialty
from schedules.models import ClinicSchedule


class ScheduleBaseTest(APITestCase):
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

        # weekdays = [day[0] for day in ClinicSchedule.Day.choices]
        # ClinicSchedule.objects.bulk_create([
        #     ClinicSchedule(clinic=self.clinic, day_name=day)
        #     for day in weekdays
        # ])
    
        