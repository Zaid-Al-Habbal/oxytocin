from django.urls import path

from .views import (
    ClinicCreateView, 
    ClinicRetrieveUpdateView,
    ClinicImageView,
    AddAssistantView,
    ListAssistantView,
    RetriveAssistantView,
    RemoveAssistantFromClinic,
    )

urlpatterns = [
    path("clinics/", ClinicCreateView.as_view(), name="clinic-create"),
    path("my-clinic/", ClinicRetrieveUpdateView.as_view(), name="clinic-retrieve-update"),
    path("my-clinic/images/", ClinicImageView.as_view(), name="clinic-images"),
    path("my-clinic/add-assistant/", AddAssistantView.as_view(), name="add-assistant"),
    path("my-clinic/assistants/", ListAssistantView.as_view(), name="list-clinic-assistants"),
    path("my-clinic/assistants/<int:pk>/", RetriveAssistantView.as_view(), name="view-clinic-assistant"),
    path("my-clinic/assistants/<int:pk>/remove/", RemoveAssistantFromClinic.as_view(), name="remove-clinic-assistant"),
]
