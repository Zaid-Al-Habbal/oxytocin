from django.urls import reverse

from rest_framework import status

from .test_schedules_base import ScheduleBaseTest

from assistants.models import Assistant

class WeekdaysScheduleTest(ScheduleBaseTest):
    def setUp(self):
        super().setUp()
        self.list_url = reverse("list-weekdays-schedules")
        
    
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