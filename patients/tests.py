from rest_framework.test import APITestCase
from django.urls import reverse
from users.models import CustomUser as User
from patients.models import Patient
from rest_framework import status

class LoginPatientTestCase(APITestCase):
    def setUp(self):
        self.login_url = reverse('login-patient')  # Make sure your url name matches
        self.password = "StrongPassw0rd!"

        # Verified patient
        self.patient = User.objects.create_user(
            phone="0999999999",
            password=self.password,
            first_name="Patient",
            last_name='xxx',
            role='patient',
            is_verified_phone=True
        )

        # Unverified patient
        self.unverified_patient = User.objects.create_user(
            phone="0888888888",
            password=self.password,
            first_name="Unverified",
            last_name='xxx',
            role='patient',
            is_verified_phone=False
        )

        # A doctor
        self.doctor = User.objects.create_user(
            phone="0777777777",
            password=self.password,
            first_name="Doctor",
            last_name='xxx',
            role='doctor',
            is_verified_phone=True
        )

    def test_login_successful_for_verified_patient(self):
        response = self.client.post(self.login_url, {
            "phone": self.patient.phone,
            "password": self.password
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_fails_with_wrong_password(self):
        response = self.client.post(self.login_url, {
            "phone": self.patient.phone,
            "password": "WrongPassword123"
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non_field_errors", response.data)

    def test_login_fails_if_not_verified_phone(self):
        response = self.client.post(self.login_url, {
            "phone": self.unverified_patient.phone,
            "password": self.password
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non_field_errors", response.data)
        self.assertIn("من فضلك, قم بتفعيل رقم جوالك أولا", response.data["non_field_errors"][0].lower())

    def test_login_fails_if_not_patient(self):
        response = self.client.post(self.login_url, {
            "phone": self.doctor.phone,
            "password": self.password
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non_field_errors", response.data)
        self.assertIn("فقط المرضى يستطيعون تسجيل الدحول هنا", response.data["non_field_errors"][0].lower())

    def test_login_fails_with_non_existing_user(self):
        response = self.client.post(self.login_url, {
            "phone": "0000000000",
            "password": "any"
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non_field_errors", response.data)




class CompletePatientRegistrationTests(APITestCase):
    def setUp(self):
        self.password = "StrongPassw0rd!"
        self.url = reverse('complete-register-patient')  # update this if needed
        
        self.verified_patient = User.objects.create_user(
            phone="0999999999",
            password=self.password,
            first_name="Patient",
            last_name="One",
            birth_date="1995-05-01",
            gender="male",
            is_verified_phone=True,
            role="patient"
        )

        self.unverified_patient = User.objects.create_user(
            phone="0888888888",
            password=self.password,
            first_name="Patient2",
            last_name="Two",
            birth_date="1992-02-02",
            gender="female",
            is_verified_phone=False,
            role="patient"
        )

        self.doctor_user = User.objects.create_user(
            phone="0777777777",
            password=self.password,
            first_name="Dr",
            last_name="User",
            birth_date="1980-01-01",
            gender="male",
            is_verified_phone=True,
            role="doctor"
        )
        self.payload = {
            "user": {
                "first_name": "NewFirstName",
                "last_name": "NewLastName",
                "gender": "male",
                "birth_date": "1995-05-01",
            },
            "location": "Damascus",
            "longitude": "36.29128",
            "latitude": "33.513806",
            "job": "Engineer",
            "blood_type": "A+",
            "medical_history": "None",
            "surgical_history": "",
            "allergies": "Peanuts",
            "medicines": "",
            "is_smoker": False,
            "is_drinker": False,
            "is_married": False,
        }

    def test_successful_patient_profile_creation(self):
        self.client.force_authenticate(self.verified_patient)

        response = self.client.post(self.url, self.payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Patient.objects.filter(user=self.verified_patient).exists())

    def test_cannot_create_profile_if_already_exists(self):
        Patient.objects.create(user=self.verified_patient, location="Damascus", longitude=36.29, latitude=33.51)

        self.client.force_authenticate(self.verified_patient)

        response = self.client.post(self.url, self.payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("لقد قمت بإنشاء ملف شخصي سابقا", str(response.data))

    def test_reject_if_phone_not_verified(self):
        self.client.force_authenticate(self.unverified_patient)

        response = self.client.post(self.url, self.payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("رقم الجوال غير مفعل", str(response.data))

    def test_reject_if_user_is_not_patient(self):
        self.client.force_authenticate(self.doctor_user)

        response = self.client.post(self.url, self.payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("ليس لديك الصلاحيات لإكمال هذه العملية", str(response.data))
        
    def test_unauthenticated_user_cannot_access(self):
        response = self.client.post(self.url, self.payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PatientProfileViewTests(APITestCase):
    def setUp(self):
        self.password = "TestPass123!"
        self.url = reverse("view-update-patient-profile")

        self.patient_user = User.objects.create_user(
            phone="0999111122",
            password=self.password,
            first_name="Patient",
            last_name="User",
            role="patient",
            is_verified_phone=True,
            gender="male",
            birth_date="1995-05-01"
        )

        self.patient = Patient.objects.create(
            user=self.patient_user,
            location="Damascus",
            longitude=36.29,
            latitude=33.51,
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

        self.doctor_user = User.objects.create_user(
            phone="0988776655",
            password=self.password,
            first_name="Doctor",
            last_name="User",
            role="doctor",
            is_verified_phone=True,
            gender="male",
            birth_date="1980-01-01"
        )

    def test_get_patient_profile_success(self):
        self.client.force_authenticate(self.patient_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user"]["first_name"], "Patient")
        self.assertEqual(response.data["location"], "Damascus")

    def test_update_patient_profile_success(self):
        self.client.force_authenticate(self.patient_user)
        response = self.client.patch(self.url, {
            "location": "Aleppo",
            "user": {
                "first_name": "UpdatedName"
            }
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.patient.refresh_from_db()
        self.assertEqual(self.patient.location, "Aleppo")
        self.assertEqual(self.patient.user.first_name, "UpdatedName")

    def test_unauthenticated_user_cannot_access(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_non_patient_role_cannot_access(self):
        self.client.force_authenticate(self.doctor_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
