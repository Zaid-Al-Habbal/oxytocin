from django.utils.timezone import now
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from .models import Appointment
from schedules.models import AvailableHour, ClinicSchedule, Clinic
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
                date=appointment.visit_date.strftime("%Y-%m-%d"),
                time=appointment.visit_time.strftime("%H:%M"),
                doctor=doctor.full_name,
            )
            send_sms.delay(patient.phone, message)

    Appointment.objects.filter(id__in=[a.id for a in appointments]).update(
        status=Appointment.Status.CANCELLED,
        cancelled_at=now(),
        cancelled_by=cancelled_by_user,
    )


def get_split_visit_times(available_hours, time_slot):
    """
    Converts available hours into discrete visit times based on the time slot.
    """
    visit_times = []
    for hour in available_hours:
        current = datetime.combine(datetime.today(), hour.start_hour)
        end = datetime.combine(datetime.today(), hour.end_hour)
        while current + timedelta(minutes=time_slot) <= end:
            visit_times.append(current.time())
            current += timedelta(minutes=time_slot)
    return visit_times


def get_next_available_slot(clinic: Clinic | int, start_datetime=None, days_ahead=30):
    """
    Return the nearest (date, time) slot that is free for the given clinic.
    """
    result = get_next_available_slots_for_clinics([clinic], start_datetime, days_ahead)
    return result.get(clinic.pk if isinstance(clinic, Clinic) else clinic, (None, None))


def get_next_available_slots_for_clinics(
    clinics: list[Clinic | int],
    start_datetime=None,
    days_ahead=30,
):
    if isinstance(clinics, list) and all(isinstance(c, int) for c in clinics):
        clinics = list(Clinic.objects.filter(pk__in=clinics))

    if not clinics:
        return {}

    start = start_datetime or now()
    start_date = start.date()

    clinic_by_id = {c.pk: c for c in clinics}
    pending_ids = set(clinic_by_id.keys())
    results: Dict[int, tuple] = {}

    for day_offset in range(days_ahead + 1):
        if not pending_ids:
            break
        target_date = start_date + timedelta(days=day_offset)
        weekday = target_date.strftime("%A").lower()
        is_today = day_offset == 0
        today_time_bound = start.time() if is_today else None

        # Fetch schedules for all pending clinics for this date
        specials = ClinicSchedule.objects.filter(
            clinic_id__in=pending_ids,
            special_date=target_date,
            is_available=True,
        )
        special_by_clinic = {s.clinic_id: s for s in specials}

        remaining_for_weekly = list(pending_ids - set(special_by_clinic.keys()))
        weekly = ClinicSchedule.objects.filter(
            clinic_id__in=remaining_for_weekly,
            day_name=weekday,
            is_available=True,
        )
        weekly_by_clinic = {s.clinic_id: s for s in weekly}

        schedule_by_clinic = {**weekly_by_clinic, **special_by_clinic}
        if not schedule_by_clinic:
            continue

        schedule_ids = [s.id for s in schedule_by_clinic.values()]
        hours_qs = AvailableHour.objects.filter(schedule_id__in=schedule_ids).order_by(
            "start_hour"
        )
        hours_by_schedule: Dict[int, list] = {}
        for h in hours_qs:
            hours_by_schedule.setdefault(h.schedule_id, []).append(h)

        # Fetch bookings for all involved clinics on this date in one go
        booked_rows = (
            Appointment.objects.filter(
                clinic_id__in=schedule_by_clinic.keys(),
                visit_date=target_date,
            )
            .exclude(status=Appointment.Status.CANCELLED)
            .values_list("clinic_id", "visit_time")
        )
        booked_by_clinic: Dict[int, set] = {}
        for clinic_id, visit_time in booked_rows:
            booked_by_clinic.setdefault(clinic_id, set()).add(visit_time)

        for clinic_id in list(pending_ids):
            schedule = schedule_by_clinic.get(clinic_id)
            if not schedule:
                continue

            available_hours = hours_by_schedule.get(schedule.id, [])
            if not available_hours:
                continue

            slot_minutes = clinic_by_id[clinic_id].time_slot_per_patient
            candidate_times = get_split_visit_times(available_hours, slot_minutes)
            if is_today:
                candidate_times = [t for t in candidate_times if t >= today_time_bound]
            if not candidate_times:
                continue

            booked_times = booked_by_clinic.get(clinic_id, set())
            for visit_time in candidate_times:
                if visit_time not in booked_times:
                    results[clinic_id] = (target_date, visit_time)
                    pending_ids.discard(clinic_id)
                    break

    # Fill unresolved clinics with (None, None)
    for clinic_id in pending_ids:
        results[clinic_id] = (None, None)

    return results
