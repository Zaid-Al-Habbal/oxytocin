from rest_framework.filters import BaseFilterBackend


class DoctorFilter(BaseFilterBackend):

    def filter_queryset(self, request, queryset, view):
        doctor_id = request.query_params.get("doctor_id")

        if doctor_id:
            queryset = queryset.filter(doctor_id=doctor_id)
        return queryset
