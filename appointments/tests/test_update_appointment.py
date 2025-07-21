from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from datetime import datetime, timedelta, date, time
from django.utils import timezone

from appointments.models import Appointment
from .test_appointments_base import AppointmentBaseTest
from users.models import CustomUser as User

class UpdateAppointmentTests(AppointmentBaseTest):
    def setUp(self):
        super().setUp()
        self.appointment = Appointment.objects.create(
            patient=self.patient_user,
            clinic=self.clinic,
            visit_date=self.special_date,
            visit_time="10:30",
            notes="I feel seek"
        )
        self.other_patient = User.objects.create_user(
            phone="0999133122",
            password=self.password,
            first_name="Other",
            last_name="Patient",
            role="patient",
            is_verified_phone=True,
            gender="male",
            birth_date="1995-05-01"
        )
        self.other_appointment = Appointment.objects.create(
            patient = self.other_patient,
            clinic= self.clinic,
            visit_date=self.special_date,
            visit_time="10:00"
        )
        self.bad_url = reverse('update-appointment', kwargs={'appointment_id': self.other_appointment.pk})
        self.url = reverse('update-appointment', kwargs={'appointment_id': self.appointment.pk})
        self.client.force_authenticate(self.patient_user)
    
    
    def build_payload(self, visit_date, visit_time):
        return {
            "visit_date": str(visit_date),
            "visit_time": str(visit_time),
            "notes": "Need a checkup",
        }
    
    def test_update_appointment_visit_time_success(self):
        payload = self.build_payload(self.special_date, "10:45")
        
        response = self.client.put(self.url, payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "waiting")
        self.assertEqual(response.data["visit_time"], "10:45:00")
        
    def test_update_appointment_visit_date_success(self):
        next_sunday = timezone.now().date() + timedelta(days=(15 - (timezone.now().weekday() + 2) % 7 or 7))
        
        payload = self.build_payload(next_sunday, "10:45")
        
        response = self.client.put(self.url, payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "waiting")
        self.assertEqual(response.data["visit_date"], str(next_sunday))
        
    def test_update_appointment_visit_time_outside_available_hour_fail(self):
        
        payload = self.build_payload(self.special_date, "06:00")
        
        response = self.client.put(self.url, payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("visit_time", response.data)

    def test_update_other_patient_appointment_fail(self):
        payload = self.build_payload(self.special_date, "10:45")
        response = self.client.put(self.bad_url, payload)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)  
        
    def test_update_appointment_visit_time_fail_when_the_new_time_already_exists(self):
        payload = self.build_payload(self.special_date, "10:00")
        
        response = self.client.put(self.url, payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("visit_time", response.data)
        