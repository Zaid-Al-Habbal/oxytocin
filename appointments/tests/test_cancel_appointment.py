from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from datetime import datetime, timedelta, date, time
from django.utils import timezone

from appointments.models import Appointment
from .test_appointments_base import AppointmentBaseTest
from users.models import CustomUser as User

class CancelAppointmentTests(AppointmentBaseTest):
    def setUp(self):
        super().setUp()
        self.appointment = Appointment.objects.create(
            patient = self.patient_user,
            clinic= self.clinic,
            visit_date=self.special_date,
            visit_time="11:00"
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
            visit_time="10:30"
        )
        self.early_appointment = Appointment.objects.create(
            patient = self.patient_user,
            clinic= self.clinic,
            visit_date=timezone.now().date() + timedelta(days=1),
            visit_time="11:30"
        )
        
        self.valid_url = reverse('cancel-appointment', kwargs={'appointment_id': self.appointment.id})
        self.not_found_url = reverse('cancel-appointment', kwargs={'appointment_id': 1000})
        self.not_your_appointment_url = reverse('cancel-appointment', kwargs={'appointment_id': self.other_appointment.id})
        self.early_url = reverse('cancel-appointment', kwargs={'appointment_id': self.early_appointment.id})
        
        self.client.force_authenticate(self.patient_user)
        
    
    def test_cancel_appointment_successfully(self):
        response = self.client.delete(self.valid_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.appointment.refresh_from_db()
        
        self.assertEqual(self.appointment.status, Appointment.Status.CANCELLED)
    
    def test_cancel_appointment_fail_when_appointment_not_exists(self):
        response = self.client.delete(self.not_found_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
    def test_cancel_appointment_fail_when_its_not_patient_appointment(self):
        response = self.client.delete(self.not_your_appointment_url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)        
        self.assertIn("You do not have permission to cancel this appointment.", str(response.data))
    
    def test_cancel_appointment_fail_when_its_early_appointment(self):
        response = self.client.delete(self.early_url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)        
        self.assertIn("لا يمكنك إلغاء موعد قبل أقل من 24 ساعة من ميعاده", str(response.data))
    
    def test_cancel_appointment_fail_when_its_status_is_not_waiting(self):
        response = self.client.delete(self.valid_url)
        response = self.client.delete(self.valid_url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Only appointments with 'waiting' status can be cancelled.", str(response.data))