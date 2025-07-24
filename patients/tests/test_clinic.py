from datetime import timedelta
from django.utils import timezone
from rest_framework.test import APITestCase
from django.contrib.gis.geos import Point
from django.urls import reverse
from clinics.models import Clinic, ClinicPatient
from common.utils import generate_test_pdf
from doctors.models import Doctor, DoctorSpecialty, Specialty
from users.models import CustomUser as User
from patients.models import Patient
from rest_framework import status


class PatientClinicBaseTestCase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.patient_user = User.objects.create_user(
            phone="0999111122",
            password="abcX123!",
            first_name="Rintaro",
            last_name="Okabe",
            role=User.Role.PATIENT.value,
            is_verified_phone=True,
            gender="male",
            birth_date="1995-05-01",
        )
        patient = Patient.objects.create(
            user=cls.patient_user,
            address="Damascus",
            location=Point(36.29, 33.51, srid=4326),
            job="Engineer",
            blood_type="A+",
            medical_history="",
            surgical_history="",
            allergies="",
            medicines="",
            is_smoker=False,
            is_drinker=False,
            is_married=False,
        )
        cls.doctor_user = User.objects.create_user(
            phone="0999111123",
            password="abcX123!",
            first_name="Kurisu",
            last_name="Makise",
            role=User.Role.DOCTOR.value,
            is_verified_phone=True,
            gender="female",
            birth_date="1995-05-01",
        )
        doctor = Doctor.objects.create(
            user=cls.doctor_user,
            about="About Test",
            education="Test",
            certificate=generate_test_pdf(),
            start_work_date=timezone.now().date() - timedelta(days=30),
            status=Doctor.Status.APPROVED.value,
        )
        main_specialty = Specialty.objects.create(
            name_en="Test1",
            name_ar="تجريبي1",
        )
        DoctorSpecialty.objects.create(
            doctor=doctor,
            specialty=main_specialty,
            university="Damascus",
        )
        clinic = Clinic.objects.create(
            doctor=doctor,
            address="Test Street",
            location=Point(44.2, 32.1, srid=4326),
            phone="011 223 3333",
        )
        cls.clinic_patient = ClinicPatient.objects.create(
            clinic=clinic,
            patient=patient,
            cost=89.8,
        )


class PatientClinicListTestCase(PatientClinicBaseTestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.path = reverse("patient-clinic-list")

    def test_list_successful(self):
        self.client.force_authenticate(self.patient_user)
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertIn("result", str(data))
        self.assertIn("clinic", str(data))

    def test_view_rejects_unauthenticated_users(self):
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_view_rejects_users_with_non_patient_role(self):
        self.client.force_authenticate(self.doctor_user)
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class PatientClinicRetrieveTestCase(PatientClinicBaseTestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.path = reverse(
            "patient-clinic-retrieve", kwargs={"pk": cls.clinic_patient.pk}
        )

    def test_retrieve_successful(self):
        self.client.force_authenticate(self.patient_user)
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertIn("clinic", str(data))
        self.assertIn("cost", str(data))

    def test_view_rejects_unauthenticated_users(self):
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_view_rejects_users_with_non_patient_role(self):
        self.client.force_authenticate(self.doctor_user)
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
