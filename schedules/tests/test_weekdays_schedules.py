from django.urls import reverse

from rest_framework import status

from .test_schedules_base import ScheduleBaseTest

from assistants.models import Assistant
from appointments.models import Appointment
from schedules.models import AvailableHour, ClinicSchedule
from datetime import time, timedelta
from django.utils import timezone

class WeekdaysScheduleTest(ScheduleBaseTest):
    def setUp(self):
        super().setUp()
        self.schedule = ClinicSchedule.objects.get(clinic=self.clinic, day_name="sunday")
        self.list_url = reverse("list-weekdays-schedules")
        self.add_url = reverse("add-available-hour-to-weekday", kwargs={"schedule_id": self.schedule.id})
        
        self.available_hour = AvailableHour.objects.create(
            schedule=self.schedule,
            start_hour=time(8, 0),
            end_hour=time(10, 0)
        )
        self.update_url = reverse("update-available-hour-to-weekday", kwargs={
            'schedule_id': self.schedule.id,
            'hour_id': self.available_hour.id
        })
    
    def test_list_clinic_weekdays_schedules_successfully(self):
        self.client.force_authenticate(user=self.assistantUser)
        
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("Sunday", str(response.data))
        self.assertIn("Monday", str(response.data))
        self.assertIn("Tuesday", str(response.data))
        self.assertIn("Wednesday", str(response.data))
        self.assertIn("Thursday", str(response.data))
        self.assertIn("Friday", str(response.data))
        self.assertIn("Saturday", str(response.data))
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
        
        self.client.force_authenticate(user=self.assistantUser)
        
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("من فضلك, قم بإنشاء ملف شحصي (مساعدة)", str(response.data))
        
    def test_add_available_hour_to_weekday_successfully(self):
        self.client.force_authenticate(user=self.assistantUser)

        response = self.client.post(self.add_url, {
            "start_hour": "13:00:00",
            "end_hour": "16:00:00"
        })
        
        # self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("available_hours", str(response.data))
        self.assertIn("start_hour", str(response.data))
        self.assertIn("end_hour", str(response.data))
    
    
    def test_add_available_hour_fail_because_of_overlapping_other_available_hours(self):
        schedule = ClinicSchedule.objects.get(pk=1)
        AvailableHour.objects.create(
            created_at="2020-02-02",
            updated_at="2020-02-02",
            schedule=schedule,
            start_hour="08:00:00",
            end_hour="12:00:00"
            )
        
        self.client.force_authenticate(user=self.assistantUser)

        response = self.client.post(self.add_url, {
            "start_hour": "11:00:00",
            "end_hour": "13:00:00"
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("هذا المجال الزمني يتقاطع مع مجالات زمنية أحرى قد قمت بإنشائها", str(response.data))
        
    def test_add_available_hour_fail_when_it_is_done_by_doctor(self):
        self.client.force_authenticate(user=self.user_doctor_clinic)
        response = self.client.post(self.add_url, {
            "start_hour": "11:00:00",
            "end_hour": "13:00:00"
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("ليس لديك الدور المطلوب.", str(response.data))
        
    def test_add_available_hour_fail_when_schedule_id_not_found(self):
        self.client.force_authenticate(user=self.assistantUser)
        fake_add_url = reverse("add-available-hour-to-weekday", kwargs={"schedule_id": 100000})
        response = self.client.post(fake_add_url, {
            "start_hour": "11:00:00",
            "end_hour": "13:00:00"
        })
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        
    def test_successful_update_available_hour(self):
        self.client.force_authenticate(user=self.assistantUser)
        
        data = {
            "start_hour": "06:00:00",
            "end_hour": "08:00:00"
        }

        response = self.client.put(self.update_url, data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['start_hour'], "06:00:00")
        self.assertEqual(response.data['end_hour'], "08:00:00")

    
    def test_update_fail_due_to_overlap(self):
        self.client.force_authenticate(user=self.assistantUser)
        
        AvailableHour.objects.create(
            schedule=self.schedule,
            start_hour=time(7, 0),
            end_hour=time(9, 0)
        )

        data = {
            "start_hour": "08:00:00",
            "end_hour": "10:00:00"
        }

        response = self.client.put(self.update_url, data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn("هذا المجال الزمني يتقاطع مع مجالات زمنية أحرى قد قمت بإنشائها", str(response.data))
        
    
    def test_appointments_cancelled_if_out_of_new_hours(self):
        self.client.force_authenticate(user=self.assistantUser)
        # Create an appointment in the range 08:30 (should be cancelled after update to 06-08)
        appointment = Appointment.objects.create(
            patient=self.patient_user,  # For simplicity, using assistant as fake patient
            clinic=self.clinic,
            visit_date="2025-06-15",
            visit_time=time(8, 30),
            status=Appointment.Status.WAITING
        )

        data = {
            "start_hour": "06:00:00",
            "end_hour": "08:00:00"
        }

        response = self.client.put(self.update_url, data, format='json')
        self.assertEqual(response.status_code, 200)

        # Refresh from DB
        appointment.refresh_from_db()
        self.assertEqual(appointment.status, Appointment.Status.CANCELLED)
        
    def test_update_fail_start_after_end(self):
        self.client.force_authenticate(user=self.assistantUser)
        
        data = {
            "start_hour": "09:00:00",
            "end_hour": "08:00:00"
        }

        response = self.client.put(self.update_url, data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn("وقت البداية يجب أن يسبق وقت النهاية", str(response.data))