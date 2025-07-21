from rest_framework import filters
from .models import Appointment
from django.db.models import Q

class AppointmentFilter(filters.BaseFilterBackend):
    
    def filter_queryset(self, request, queryset, view):
        user = request.user
        queryset = Appointment.objects.filter(patient=user)

        status_param = request.query_params.get("status")
        if status_param:
            statuses = [s.strip() for s in status_param.split(",")]
            queryset = queryset.filter(status__in=statuses)

        return queryset.select_related(
            'clinic__doctor__user'
        ).order_by('visit_date', 'visit_time') 