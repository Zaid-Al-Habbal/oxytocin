from abc import abstractmethod
from unfold.components import BaseComponent, register_component
from doctors.models import Doctor
from users.models import CustomUser as User
from django.utils.translation import gettext as _
from django.db.models import Count, Q
from appointments.models import Appointment
from django.utils import timezone
import calendar
import json


@register_component
class AppointmentsCohortComponent(BaseComponent):
    def get_color_levels(self):
        return [
            "bg-primary-50 dark:bg-primary-800 text-white",
            "bg-primary-100 dark:bg-primary-400 text-white",
            "bg-primary-200 dark:bg-primary-200 text-white",
            "bg-primary-400 dark:bg-primary-100 text-white",
            "bg-primary-800 dark:bg-primary-50 text-white",
        ]

    def get_queryset(self):
        return (
            Doctor.objects.not_deleted()
            .approved()
            .with_clinic_appointments()
            .annotate(
                appointments_count=Count(
                    "clinic__appointments",
                    filter=~Q(
                        clinic__appointments__status=Appointment.Status.CANCELLED.value
                    )
                    & Q(
                        clinic__appointments__visit_date__year=timezone.localdate().year
                    ),
                    distinct=True,
                )
            )
            .distinct()
            .order_by("-appointments_count")[:7]
        )

    def get_headers(self):
        return [
            {
                "title": doctor.user.full_name,
                "subtitle": doctor.appointments_count or "0",
            }
            for doctor in self.doctors
        ]

    def get_row(self, **kwargs):
        month = kwargs["month"]
        # Fetch counts for all selected doctors in a single query for this date
        doctor_user_ids = [doctor.user_id for doctor in self.doctors]
        per_month_rows = (
            Doctor.objects.not_deleted()
            .approved()
            .with_clinic_appointments()
            .filter(user_id__in=doctor_user_ids)
            .annotate(
                appointments_count=Count(
                    "clinic__appointments",
                    filter=~Q(
                        clinic__appointments__status=Appointment.Status.CANCELLED.value
                    )
                    & Q(clinic__appointments__visit_date__month=month),
                    distinct=True,
                )
            )
            .values("user_id", "appointments_count")
        )

        appointments_count_by_user_id = {
            row["user_id"]: row["appointments_count"] for row in per_month_rows
        }

        cols = []
        total_appointments_count = 0
        for doctor in self.doctors:
            appointments_count = appointments_count_by_user_id.get(doctor.user_id, 0)
            cols.append(
                {
                    "value": appointments_count,
                }
            )
            total_appointments_count += appointments_count

        return {
            "header": {
                "title": _(calendar.month_name[month]),
                "subtitle": total_appointments_count or "0",
            },
            "cols": cols,
        }

    def get_data(self):
        self.doctors = list(self.get_queryset())
        rows = []
        current_month = 1
        while current_month <= 12:
            row = self.get_row(month=current_month)
            rows.append(row)
            current_month += 1

        value_to_color = self.build_value_to_color_mapping(rows)

        for row in rows:
            for col in row["cols"]:
                col["color"] = value_to_color[col["value"]]
                col["value"] = col["value"] or "0"

        return {
            "headers": self.get_headers(),
            "rows": rows,
        }

    def build_value_to_color_mapping(self, rows):
        unique_values_desc = sorted(
            {col["value"] for row in rows for col in row["cols"]},
            reverse=True,
        )

        color_levels = self.get_color_levels()

        value_to_color = {}
        for idx, value in enumerate(unique_values_desc):
            if idx < len(color_levels) - 1 and value > 0:
                color_index = len(color_levels) - (idx + 1)
            else:
                color_index = 0
            value_to_color[value] = color_levels[color_index]
        return value_to_color

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"data": self.get_data()})
        return context


class UsersLineComponent(BaseComponent):

    @property
    @abstractmethod
    def role(self):
        pass

    def get_queryset(self):
        return (
            User.objects.filter(
                role=self.role,
                created_at__year=timezone.localdate().year,
            )
            .not_deleted()
            .verified_phone()
        )

    def get_count(self):
        print(self.get_queryset().count())
        return self.get_queryset().count()

    def get_data(self, **kwargs):
        month = kwargs["month"]
        queryset = self.get_queryset().filter(created_at__month=month)
        return [1, queryset.count()]

    def get_labels(self):
        return [_(calendar.month_name[month]) for month in range(1, 13)]

    def get_datasets(self):
        self.users = list(self.get_queryset())
        data = []
        current_month = 1
        while current_month <= 12:
            data.append(self.get_data(month=current_month))
            current_month += 1

        return [
            {
                "data": data,
                "borderColor": "var(--color-primary-500)",
            }
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        data = json.dumps(
            {
                "labels": self.get_labels(),
                "datasets": self.get_datasets(),
            }
        )
        context.update({"data": data})
        return context


@register_component
class PatientsLineComponent(UsersLineComponent):
    role = User.Role.PATIENT


@register_component
class DoctorsLineComponent(UsersLineComponent):
    role = User.Role.DOCTOR


@register_component
class AssistantsLineComponent(UsersLineComponent):
    role = User.Role.ASSISTANT
