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


class DeleteWorkingHoursTestCase(ScheduleBaseTest):
    def setUp(self):
        super().setUp()
        
        self.weekday_schedule = ClinicSchedule.objects.get(clinic=self.clinic, day_name=timezone.now().strftime("%A").lower(),)
        
        AvailableHour.objects.bulk_create([
            AvailableHour(schedule=self.weekday_schedule, start_hour=time(8, 0), end_hour=time(12, 0)),
            AvailableHour(schedule=self.weekday_schedule, start_hour=time(14, 0), end_hour=time(18, 0)),
        ])
        
        self.special_date = (timezone.now() + timedelta(days=3)).date()
        
        # Appointment inside the period to be deleted
        self.appointment_in_range = Appointment.objects.create(
            clinic=self.clinic,
            patient=self.patient_user,
            visit_date=self.special_date,
            visit_time=time(9, 0),
            status=Appointment.Status.WAITING,
        )
        
        # Appointment outside the period
        self.appointment_out_range = Appointment.objects.create(
            clinic=self.clinic,
            patient=self.patient_user,
            visit_date=self.special_date,
            visit_time=time(19, 0),
            status=Appointment.Status.WAITING,
        )
        
        self.url = reverse("delete-working-hour")
        
        self.client.force_authenticate(user=self.assistantUser)

        
    
    def test_successful_delete_working_hours_creates_special_date(self):
        data = {
            "special_date": self.special_date,
            "start_working_hour": "08:00:00",
            "end_working_hour": "10:00:00",
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        schedule = ClinicSchedule.objects.get(clinic=self.clinic, special_date=self.special_date)
        self.assertTrue(schedule.is_available)

    def test_delete_with_invalid_hour_range(self):
        data = {
            "special_date": self.special_date,
            "start_working_hour": "12:00:00",
            "end_working_hour": "10:00:00",  # Invalid range
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("وقت البداية يجب أن يسبق وقت النهاية", str(response.data))
        
    def test_delete_with_past_special_date(self):
        past_date = (timezone.now() - timedelta(days=1)).date()
        data = {
            "special_date": past_date,
            "start_working_hour": "08:00:00",
            "end_working_hour": "10:00:00",
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("التاريخ الخاص يجب أن يكون في المستقبل", str(response.data))
        
    def test_appointment_in_deleted_range_cancelled(self):
        data = {
            "special_date": self.special_date,
            "start_working_hour": "08:00:00",
            "end_working_hour": "10:00:00",
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.appointment_in_range.refresh_from_db()
        self.assertEqual(self.appointment_in_range.status, Appointment.Status.CANCELLED)
        
    def test_appointment_outside_deleted_range_not_cancelled(self):
        data = {
            "special_date": self.special_date,
            "start_working_hour": "08:00:00",
            "end_working_hour": "10:00:00",
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.appointment_out_range.refresh_from_db()
        self.assertEqual(self.appointment_out_range.status, Appointment.Status.WAITING)

    def test_unauthenticated_access_denied(self):
        self.client.logout()
        data = {
            "special_date": self.special_date,
            "start_working_hour": "08:00:00",
            "end_working_hour": "10:00:00",
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
    def test_non_assistant_user_forbidden(self):
        self.client.logout()
        self.client.force_authenticate(user=self.patient_user)
        data = {
            "special_date": self.special_date,
            "start_working_hour": "08:00:00",
            "end_working_hour": "10:00:00",
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)