from django.urls import path

from .views import (
    ClinicCreateView, 
    ClinicRetrieveUpdateView,
    ClinicImageView,
    ClinicNearestListView,
    AddAssistantView,
    ListAssistantView,
    RetrieveAssistantView,
    RemoveAssistantFromClinic,
    ClinicPatientListView,
    ClinicPatientRetrieveUpdateView,
)

urlpatterns = [
    path("", ClinicCreateView.as_view(), name="clinic-create"),
    path("nearest/", ClinicNearestListView.as_view(), name="clinic-nearest"),
    path("my-clinic/", ClinicRetrieveUpdateView.as_view(), name="clinic-retrieve-update"),
    path("my-clinic/images/", ClinicImageView.as_view(), name="clinic-images"),
    path("my-clinic/add-assistant/", AddAssistantView.as_view(), name="add-assistant"),
    path("my-clinic/assistants/", ListAssistantView.as_view(), name="list-clinic-assistants"),
    path("my-clinic/assistants/<int:pk>/", RetrieveAssistantView.as_view(), name="view-clinic-assistant"),
    path("my-clinic/assistants/<int:pk>/remove/", RemoveAssistantFromClinic.as_view(), name="remove-clinic-assistant"),
    path("patients/", ClinicPatientListView.as_view(), name="clinic-patient-list"),
    path("patients/<int:pk>/", ClinicPatientRetrieveUpdateView.as_view(), name="clinic-patient-retrieve-update"),
]
