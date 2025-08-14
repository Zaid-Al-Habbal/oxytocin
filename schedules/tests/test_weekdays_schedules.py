from django.urls import reverse

from rest_framework import status

from .test_schedules_base import ScheduleBaseTest

from assistants.models import Assistant
from appointments.models import Appointment
from schedules.models import AvailableHour, ClinicSchedule
from datetime import time, timedelta
from django.utils import timezone
from users.models import CustomUser as User
from doctors.models import Doctor, Specialty, DoctorSpecialty
from clinics.models import Clinic  
from common.utils import generate_test_pdf
from django.contrib.gis.geos import Point


class WeekdaysScheduleTest(ScheduleBaseTest):
    def setUp(self):
        super().setUp()
        self.schedule = ClinicSchedule.objects.get(clinic=self.clinic, day_name="sunday")
        self.list_url = reverse("list-weekdays-schedules")
        self.replace_url = reverse("replace-available-hours-of-weekday", kwargs={'schedule_id': self.schedule.id})
        
        self.client.force_authenticate(user=self.assistantUser)
    
    def test_list_clinic_weekdays_schedules_successfully(self):
        
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("الأحد", str(response.data))
        self.assertIn("الاثنين", str(response.data))
        self.assertIn("الثلاثاء", str(response.data))
        self.assertIn("الأربعاء", str(response.data))
        self.assertIn("الخميس", str(response.data))
        self.assertIn("الجمعة", str(response.data))
        self.assertIn("السبت", str(response.data))
        self.assertIn("available_hours", str(response.data))
        
    def test_list_clinic_weekdays_schedules_fail_if_assistant_not_connect_to_clinic(self):
        self.assistant.clinic = None
        self.assistant.save()
        
        self.client.force_authenticate(user=self.assistantUser)
        
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("قم بالإنضمام لعيادة أولا", str(response.data))
        
    def test_list_clinic_weekdays_schedules_fail_if_assistant_did_not_create_profile(self):
        Assistant.objects.get(user=self.assistantUser).delete()
        self.assistantUser.refresh_from_db()
                
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("من فضلك, قم بإنشاء ملف شحصي (مساعدة)", str(response.data))
        
    def test_replace_available_hours_success(self):        
        valid_data = [
            {"start_hour": "08:00:00", "end_hour": "10:00:00"},
            {"start_hour": "11:00:00", "end_hour": "13:00:00"},
        ]

        response = self.client.put(self.replace_url, data=valid_data, format='json')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['available_hours']), 2)
        self.assertEqual(response.data['day_name_display'], 'الأحد')
        
    def test_replace_available_hours_overlap_failure(self):
        invalid_data = [
            {"start_hour": "08:00:00", "end_hour": "10:00:00"},
            {"start_hour": "09:30:00", "end_hour": "11:00:00"},  # Overlaps with first
        ]

        response = self.client.put(self.replace_url, data=invalid_data, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertIn("أوقات العمل لا يمكن أن تكون متقاطعة", str(response.data))
        
    def test_replace_available_hours_start_after_end_failure(self):
        schedule = ClinicSchedule.objects.create(
            clinic=self.clinic,
            day_name='tuesday'
        )

        invalid_data = [
            {"start_hour": "08:00:00", "end_hour": "10:00:00"},
            {"start_hour": "12:00:00", "end_hour": "10:00:00"}  # Invalid: start after end
        ]

        response = self.client.put(self.replace_url, data=invalid_data, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertIn("وقت البداية يجب أن يسبق وقت النهاية", str(response.data))

    def test_replace_available_hours_empty_list_failure(self):
        response = self.client.put(self.replace_url, data=[], format='json')

        self.assertEqual(response.status_code, 400)
        self.assertIn("يجب أن ترسل زوج واحد من ساعات العمل على الأقل", str(response.data))

    def test_replace_available_hours_unauthorized_user(self):
        self.client.force_authenticate(user=self.patient_user)  # Not an assistant

        valid_data = [
            {"start_hour": "08:00:00", "end_hour": "10:00:00"},
        ]

        response = self.client.put(self.replace_url, data=valid_data, format='json')

        self.assertEqual(response.status_code, 403)  # Forbidden for non-assistants

    def test_replace_available_hours_cancels_appointments(self):
        # Create an appointment in the old range
        appointment = Appointment.objects.create(
            clinic=self.clinic,
            patient=self.patient_user,
            visit_date=timezone.now().date() + timedelta(days=(15 - (timezone.now().weekday() + 2) % 7 or 7)),
            visit_time="09:00:00",
            status=Appointment.Status.WAITING
        )

        new_hours = [
            {"start_hour": "11:00:00", "end_hour": "13:00:00"},
        ]

        response = self.client.put(self.replace_url, data=new_hours, format='json')
        self.assertEqual(response.status_code, 200)

        # Refresh from DB
        appointment.refresh_from_db()
        self.assertEqual(appointment.status, Appointment.Status.CANCELLED)

    def test_replace_available_hours_schedule_other_clinic_forbidden(self):
        other_user = User.objects.create_user(
            phone="0999555666",
            password=self.password,
            role=User.Role.DOCTOR
        )
        other_doctor = Doctor.objects.create(user=other_user, **{
            "about": "other doc",
            "education": "other edu",
            "start_work_date": timezone.now().date() - timedelta(days=60),
            "certificate": generate_test_pdf(),
            "status": Doctor.Status.APPROVED,
        })
        other_clinic = Clinic.objects.create(
            doctor=other_doctor,
            address= "Test Street",
            location=  Point(44.2, 32.1, srid=4326),
            phone="011 555 5555"
        )
        other_schedule = ClinicSchedule.objects.create(
            clinic=other_clinic,
            day_name='saturday'
        )

        fake_replace_url = reverse("replace-available-hours-of-weekday", kwargs={'schedule_id': other_schedule.id})
        valid_data = [
            {"start_hour": "09:00:00", "end_hour": "11:00:00"},
        ]

        response = self.client.put(fake_replace_url, data=valid_data, format='json')
        self.assertEqual(response.status_code, 404)  # Should not access another clinic's schedule
