from rest_framework import status
from doctors.models import Doctor
from .test_assistant_base import TestAssistantBase


class AddAssistantToClinicTest(TestAssistantBase):

    def test_add_assistant_successfully(self):
        # Authentication
        self.client.force_authenticate(user=self.user_doctor_clinic)

        response = self.client.post(self.url, {"assistant_phone": "0999888777"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assistant.refresh_from_db()

        self.assertEqual(self.assistant.clinic, self.clinic)
        self.assertIsNotNone(self.assistant.joined_clinic_at)
        self.assertEqual(response.data["detail"], "تمت إضافة المساعدة بنجاح")

    def test_add_assistant_already_linked(self):
        # Authentication
        self.client.force_authenticate(user=self.user_doctor_clinic)

        self.assistant.clinic = self.clinic
        self.assistant.save()

        response = self.client.post(self.url, {"assistant_phone": "0999888777"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("المساعدة مرتبطة بعيادة أخرى", str(response.data))

    def test_add_non_existing_assistant(self):
        # Authentication
        self.client.force_authenticate(user=self.user_doctor_clinic)

        response = self.client.post(self.url, {"assistant_phone": "0900000000"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("ليس هناك مساعدة بهذا الرقم", str(response.data))

    def test_add_assistant_by_doctor_without_clinic(self):
        # Authentication
        self.client.force_authenticate(user=self.user_doctor)
        response = self.client.post(self.url, {"assistant_phone": "0999888777"})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assistant.refresh_from_db()

        self.assertIsNone(self.assistant.clinic)
        self.assertIsNone(self.assistant.joined_clinic_at)
        self.assertIn("عيادة الطبيب غير مكتملة.", str(response.data))

    def test_add_assistant_by_not_approved_doctor(self):
        # Authentication
        self.client.force_authenticate(user=self.user_doctor_clinic)
        self.doctor_with_clinic.status = Doctor.Status.PENDING
        self.doctor_with_clinic.save()

        response = self.client.post(self.url, {"assistant_phone": "0999888777"})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assistant.refresh_from_db()

        self.assertIsNone(self.assistant.clinic)
        self.assertIsNone(self.assistant.joined_clinic_at)
        self.assertIn("حسابك قيد المراجعة. يُرجى انتظار الموافقة.", str(response.data))
