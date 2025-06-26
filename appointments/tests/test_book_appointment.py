from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from datetime import datetime, timedelta, date, time
from django.utils import timezone

from appointments.models import Appointment
from .test_appointments_base import AppointmentBaseTest

class BookAppointmentTests(AppointmentBaseTest):
    def setUp(self):
        super().setUp()
        self.url = reverse('book-appointment', kwargs={'clinic_id': self.clinic.pk})
    
    
    def build_payload(self, visit_date, visit_time):
        return {
            "visit_date": str(visit_date),
            "visit_time": str(visit_time),
            "note": "Need a checkup",
        }
    
    def test_book_appointment_weekday_success(self):
        self.client.force_authenticate(self.patient_user)
        next_sunday = timezone.now().date() + timedelta(days=(15 - (timezone.now().weekday() + 2) % 7 or 7))
        
        payload = self.build_payload(next_sunday, "08:30")
        
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["doctor_id"], self.clinic.pk)
        self.assertEqual(response.data["status"], "waiting")
        
    def test_book_appointment_special_date_success(self):
        self.client.force_authenticate(self.patient_user)
        payload = self.build_payload(self.special_date, "10:30")

        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["visit_date"], str(self.special_date))
        self.assertEqual(response.data["doctor_id"], self.clinic.pk)
        
    def test_book_outside_available_hour(self):
        self.client.force_authenticate(self.patient_user)
        next_sunday = timezone.now().date() + timedelta(days=(15 - (timezone.now().weekday() + 2) % 7 or 7))
        
        payload = self.build_payload(next_sunday, "06:00")
        
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("visit_time", response.data)
        
    def test_book_appointment_weekday_success(self):
        self.client.force_authenticate(self.patient_user)
        next_sunday = timezone.now().date() + timedelta(days=(15 - (timezone.now().weekday() + 2) % 7 or 7))
        
        payload = self.build_payload(next_sunday, "08:30")
        
        response = self.client.post(self.url, payload)
        response = self.client.post(self.url, payload)
        
        self.assertEqual(response.status_code, 400)
        self.assertIn("هذا الوقت محجوز من قبل مريض آخر", response.data['visit_time'])
        
    def test_book_unauthenticated(self):
        payload = self.build_payload(timezone.now().date(), "08:30")
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 401)

    
    def test_doctor_cannot_book_appointment(self):
        self.client.force_authenticate(self.user_doctor_clinic)
        payload = self.build_payload(timezone.now().date(), "08:30")

        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 403)
        
    def test_rebooking_cancelled_appointment_slot(self):
        Appointment.objects.create(
            patient=self.patient_user,
            clinic=self.clinic,
            visit_date=self.special_date,
            visit_time=time(10, 0),
            status=Appointment.Status.CANCELLED
        )
        self.client.force_authenticate(self.patient_user)
        response = self.client.post(self.url, self.build_payload(self.special_date, "10:00"))
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["visit_date"], str(self.special_date))
        self.assertEqual(response.data["doctor_id"], self.clinic.pk)