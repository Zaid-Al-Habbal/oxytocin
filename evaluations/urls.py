from django.urls import path

from evaluations import views

app_name = "evaluations"

urlpatterns = [
    path(
        "",
        views.EvaluationListCreateView.as_view(),
        name="evaluation-list-create",
    ),
    path(
        "<int:pk>/",
        views.EvaluationDestroyView.as_view(),
        name="evaluation-destroy",
    ),
]
