from django.utils.timezone import now
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from .models import Appointment
from users.tasks import send_sms
from datetime import datetime, timedelta, time
from typing import List, Dict

def cancel_appointments_with_notification(appointments, cancelled_by_user):
    """
    Cancels the given appointments and sends SMS notifications to patients
    if the environment is not TESTING.
    
    Args:
        appointments (QuerySet or list): List or queryset of Appointment instances.
        cancelled_by_user (User): The user responsible for the cancellation.
    """
    if not appointments:
        return  # Nothing to cancel

    if not settings.TESTING:
        for appointment in appointments:
            patient = appointment.patient
            doctor = appointment.clinic.doctor.user
            message = _(
                "Dear {patient},\n your appointment on {date} at {time} with Dr. {doctor} has been cancelled due to clinic schedule changes.\n"
                "Please reschedule through our app. We apologize for any inconvenience."
            ).format(
                patient=patient.full_name,
                date=appointment.visit_date.strftime('%Y-%m-%d'),
                time=appointment.visit_time.strftime('%H:%M'),
                doctor=doctor.full_name
            )
            send_sms.delay(patient.phone, message)

    Appointment.objects.filter(id__in=[a.id for a in appointments]).update(
        status=Appointment.Status.CANCELLED,
        cancelled_at=now(),
        cancelled_by=cancelled_by_user
    )



def generate_start_times(available_hours: List[Dict[str, time]], time_slot_per_patient: int) -> List[time]:
    """
    Generate start times from available hour blocks and time slot duration.

    :param available_hours: List of dicts with 'start_hour' and 'end_hour' as datetime.time
    :param time_slot_per_patient: Slot duration in minutes
    :return: List of datetime.time objects for start times
    """
    all_start_times = []

    for hour_block in available_hours:
        start = datetime.combine(datetime.today(), hour_block["start_hour"])
        end = datetime.combine(datetime.today(), hour_block["end_hour"])
        delta = timedelta(minutes=time_slot_per_patient)

        while start + delta <= end:
            all_start_times.append(start.time())
            start += delta

    return all_start_times
