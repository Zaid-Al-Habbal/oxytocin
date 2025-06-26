from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from datetime import datetime, timedelta, date, time
from django.utils import timezone

from .test_appointments_base import AppointmentBaseTest

class ListClinicVisitTimesTests(AppointmentBaseTest):
    def setUp(self):
        super().setUp()
        self.url = reverse('list-clinic-visit-times', kwargs={'clinic_id': self.clinic.pk},  )
        
    
    def test_weekday_schedule_visit_times(self):

        next_sunday = timezone.now().date() + timedelta(days=(15 - (timezone.now().weekday() + 2) % 7 or 7))
        response = self.client.get(f"{self.url}?visitDate={next_sunday}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("08:00", str(response.data))
        self.assertIn("08:15", str(response.data))
        self.assertIn("14:30", str(response.data))
        self.assertIn("is_booked", str(response.data))
        

    def test_special_date_schedule_visit_times(self):

        response = self.client.get(f"{self.url}?visitDate={self.special_date}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("10:00", str(response.data))
        self.assertIn("10:15", str(response.data))
        self.assertIn("16:30", str(response.data))
        self.assertIn("is_booked", str(response.data))
        
    