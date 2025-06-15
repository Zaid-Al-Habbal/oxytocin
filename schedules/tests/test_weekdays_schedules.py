from django.urls import reverse

from rest_framework import status

from .test_schedules_base import ScheduleBaseTest

from assistants.models import Assistant
from schedules.models import AvailableHour, ClinicSchedule

class WeekdaysScheduleTest(ScheduleBaseTest):
    def setUp(self):
        super().setUp()
        schedule = ClinicSchedule.objects.get(clinic=self.clinic, day_name="sunday")
        self.list_url = reverse("list-weekdays-schedules")
        self.add_url = reverse("add-available-hour-to-weekday", kwargs={"schedule_id": schedule.id})
        
    
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
        
        