from django.urls import path

from archives import views


urlpatterns = [
    path("", views.ArchivePatientListView.as_view(), name="archive-patient-list"),
    
    path("<int:patient_pk>/", views.ArchiveListView.as_view(), name="archive-list"),
    path("<int:patient_pk>/create/", views.ArchiveCreateView.as_view(), name="archive-create"),
    
    path("detail/<int:pk>/", views.ArchiveRetrieveView.as_view(), name="archive-retrieve"),
    path("update/<int:pk>/", views.ArchiveUpdateView.as_view(), name="archive-update"),
    path("delete/<int:pk>/", views.ArchiveDestroyView.as_view(), name="archive-destroy"),
]
