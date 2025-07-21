from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from datetime import datetime, timedelta, date, time
from django.utils import timezone

from appointments.models import Appointment
from .test_appointments_base import AppointmentBaseTest
from users.models import CustomUser as User

class ChangeAppointmentStatusTests(AppointmentBaseTest):
    def setUp(self):
        super().setUp()
        self.appointment = Appointment.objects.create(
            patient=self.patient_user,
            clinic=self.clinic,
            visit_date=self.special_date,
            visit_time="10:30",
            notes="I feel seek"
        )
        self.url = reverse('change-appointment-status', kwargs={'appointment_id': self.appointment.pk})
        self.client.force_authenticate(self.assistantUser)
    
    
    def build_payload(self, status):
        return {
            "status": str(status)
        }
        
    def test_change_appointment_status_from_waiting_to_in_consultation(self):
        payload = self.build_payload(Appointment.Status.IN_CONSULTATION)
        
        response = self.client.patch(self.url, payload)
        
        self.assertEqual(response.status_code, 200)
        self.appointment.refresh_from_db()
        self.assertIsNotNone(self.appointment.actual_start_time)
    
    def test_change_appointment_status_from_in_consultation_to_completed(self):
        payload = self.build_payload(Appointment.Status.COMPLETED)
        self.appointment.status = Appointment.Status.IN_CONSULTATION
        self.appointment.save()
        
        response = self.client.patch(self.url, payload)
        
        self.assertEqual(response.status_code, 200)
        self.appointment.refresh_from_db()
        self.assertIsNotNone(self.appointment.actual_end_time)
        
    def test_change_appointment_status_from_waiting_to_absent(self):
        payload = self.build_payload(Appointment.Status.ABSENT)
        
        response = self.client.patch(self.url, payload)
        
        self.assertEqual(response.status_code, 200)
        
    def test_change_appointment_status_from_in_consultation_to_absent(self):
        payload = self.build_payload(Appointment.Status.ABSENT)
        self.appointment.status = Appointment.Status.IN_CONSULTATION
        self.appointment.save()
        
        response = self.client.patch(self.url, payload)
        
        self.assertEqual(response.status_code, 400)
        self.assertIn("Can only mark as absent from waiting.", str(response.data))
        
    def test_change_appointment_status_from_in_consultation_to_waiting(self):
        payload = self.build_payload(Appointment.Status.WAITING)
        self.appointment.status = Appointment.Status.IN_CONSULTATION
        self.appointment.save()
        
        response = self.client.patch(self.url, payload)
        
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid status change.", str(response.data))
        
    def test_change_appointment_status_from_completed_to_absent(self):
        payload = self.build_payload(Appointment.Status.ABSENT)
        self.appointment.status = Appointment.Status.COMPLETED
        self.appointment.save()
        
        response = self.client.patch(self.url, payload)
        
        self.assertEqual(response.status_code, 400)
        self.assertIn("Can only mark as absent from waiting.", str(response.data))