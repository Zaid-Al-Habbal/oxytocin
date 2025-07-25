from rest_framework.filters import BaseFilterBackend


class ArchiveSpecialtyFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        filter = request.query_params.get("specialties")
        if filter:
            specialties = [v.strip() for v in filter.split(",") if v.strip()]
            queryset = queryset.filter(specialty_id__in=specialties)
        return queryset
