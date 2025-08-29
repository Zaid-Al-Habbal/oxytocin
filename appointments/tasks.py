from celery import shared_task
from django.utils.timezone import make_aware
from datetime import datetime, timedelta
from django.utils.translation import gettext as _

from users.tasks import send_sms
from appointments.models import Appointment
from appointments.models import Appointment

@shared_task
def send_appointment_reminder(appointment_id):
    try:
        appointment = Appointment.objects.select_related("patient", "clinic").get(id=appointment_id)
        patient = appointment.patient
        if not patient or not patient.phone:
            return f"Appointment {appointment_id} has no patient or phone number"
        message = _(
              "Reminder: You have an appointment at {doctor} clinic "
              "on {date} at {time}. Please arrive on time."
          ).format(
              doctor=appointment.clinic.doctor.user.full_name,
              date=appointment.visit_date,
              time=appointment.visit_time,
          )
        send_sms.delay(patient.phone, message)  # enqueue SMS sending
        return f"Reminder sent to {patient.phone} for appointment {appointment_id}"
    except Appointment.DoesNotExist:
        return f"Appointment {appointment_id} not found"
