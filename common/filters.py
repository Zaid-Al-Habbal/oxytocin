from django.db.models.functions import Greatest
from django.contrib.postgres.search import TrigramSimilarity

from rest_framework.filters import SearchFilter


class TrigramSearchFilter(SearchFilter):
    search_param = "query"
    similarity_threshold = 0.2

    def filter_queryset(self, request, queryset, view):
        search_term = request.query_params.get(self.search_param)
        if not search_term or len(search_term) < 3:
            return queryset

        search_fields = self.get_search_fields(view, request)
        if not search_fields:
            return queryset

        similarities = [
            TrigramSimilarity(field, search_term) for field in search_fields
        ]
        queryset = (
            queryset.annotate(similarity=Greatest(*similarities))
            .filter(similarity__gt=self.similarity_threshold)
            .order_by("-similarity")
        )
        return queryset
