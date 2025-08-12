from django.urls import path

from archives import views


urlpatterns = [
    path("", views.ArchiveListCreateView.as_view(), name="archive-list-create"),
    path(
        "<int:pk>/",
        views.ArchiveRetrieveUpdateDestroyView.as_view(),
        name="archive-retrieve-update-destroy",
    ),
]
