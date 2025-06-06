from rest_framework.test import APITestCase
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from django.urls import reverse

from common.utils import generate_test_pdf

from users.models import CustomUser as User
from clinics.models import Clinic  
from assistants.models import Assistant
from doctors.models import Doctor, Specialty, DoctorSpecialty


class AddAssistantToClinicTest(APITestCase):
    def setUp(self):
        self.list_url = reverse("list-clinic-assistants")
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

        self.main_specialty1 = Specialty.objects.create(
            name_en="Test1",
            name_ar="تجريبي1",
        )
        self.subspecialty1 = Specialty.objects.create(
            name_en="Test2",
            name_ar="تجريبي2",
            parent=self.main_specialty1,
        )
        self.subspecialty2 = Specialty.objects.create(
            name_en="Test3",
            name_ar="تجريبي3",
            parent=self.main_specialty1,
        )
        self.main_specialty2 = Specialty.objects.create(
            name_en="Test4",
            name_ar="تجريبي4",
        )
        self.subspecialty3 = Specialty.objects.create(
            name_en="Test5",
            name_ar="تجريبي5",
            parent=self.main_specialty2,
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

        self.data = {
            "location": "Test Street",
            "longitude": 39.1,
            "latitude": 55.5,
            "phone": "011 224 4531",
        }
        self.user2 = User.objects.create_user(
            first_name="user",
            last_name="assistant",
            phone="0999888777",
            is_verified_phone=True,
            password=self.password,
            role=User.Role.ASSISTANT,
        )
        
        self.assistant = Assistant.objects.create(
            user=self.user2,
            education="bla bla bla",
            start_work_date="2020-2-2",
            clinic=self.clinic,
            joined_clinic_at=timezone.now().date()
        )
        self.leave_url = reverse("leave-myclinic")
    
    def test_assistant_can_leave_clinic_successfully(self):
        self.client.force_authenticate(user=self.user2)
        
        response = self.client.delete(self.leave_url)
        self.assistant.refresh_from_db()
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(self.assistant.clinic)
        self.assertIsNone(self.assistant.joined_clinic_at)
        self.assertIn(
             "لقد غادرت العيادة, بنجاح", str(response.data)
        )
    
    def test_fail_to_leave_clinic_if_assistant_not_connected_to_anyone(self):
        self.client.force_authenticate(user=self.user2)
        self.assistant.clinic = None
        self.assistant.joined_clinic_at = None
        
        response = self.client.delete(self.leave_url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn(
             "أنت غير مرتبط بأي عيادة", str(response.data)
        )