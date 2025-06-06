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
from .test_assistant_base import TestAssistantBase


class RemoveListAssistantToClinicTest(TestAssistantBase):
    def setUp(self):
        super().setUp()
        
        self.remove_url = reverse("remove-clinic-assistant", kwargs={ "pk": self.user2.id})
        self.bad_remove_url = reverse("remove-clinic-assistant", kwargs={ "pk": 10000})
        self.view_url = reverse("view-clinic-assistant", kwargs={ "pk": self.user2.id})
        
        self.assistant.clinic = self.clinic
        self.assistant.save()
        
    #test remove assistant successfully
    def test_remove_assistant_successfully(self):
        self.client.force_authenticate(user=self.user_doctor_clinic)
        
        response = self.client.delete(self.remove_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assistant.refresh_from_db()

        self.assertIsNone(self.assistant.clinic)
        self.assertIsNone(self.assistant.joined_clinic_at)
        self.assertIn(
             "تمت إزالة المساعدة من العيادة", str(response.data)
        )
    
    def test_unable_to_remove_an_assistant_not_exists(self):
        self.client.force_authenticate(user=self.user_doctor_clinic)
        
        response = self.client.delete(self.bad_remove_url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn(
             "المساعدة غير موجودة", str(response.data)
        )
    
    def test_list_clinic_assistants(self):
        self.client.force_authenticate(user=self.user_doctor_clinic)
        
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for assistant_obj in response.data:
            self.assertIn("full_name", assistant_obj)
            self.assertIn("phone", assistant_obj)
            self.assertIn("joined_clinic_at", assistant_obj)
            self.assertIn("image", assistant_obj)
            
    def test_view_clinic_assistant(self):
        self.client.force_authenticate(user=self.user_doctor_clinic)
        
        response = self.client.get(self.view_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("user", response.data)
        self.assertIn("about", response.data)
        self.assertIn("education", response.data)
        self.assertIn("joined_clinic_at", response.data)
        self.assertIn("years_of_experience", response.data)
        self.assertIn("start_work_date", response.data)
