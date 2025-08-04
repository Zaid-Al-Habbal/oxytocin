from django.urls import path

from evaluations import views


urlpatterns = [
    path(
        "",
        views.EvaluationListCreateView.as_view(),
        name="evaluation-list-create",
    ),
    path(
        "<int:pk>/",
        views.EvaluationRetrieveUpdateView.as_view(),
        name="evaluation-retrieve-update",
    ),
]
