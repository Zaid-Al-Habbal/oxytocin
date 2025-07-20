from django.urls import path

from .views import (
    LoginPatientView,
    CompletePatientRegistrationView,
    PatientProfileView,
    PatientSpecialtyAccessListCreateView,
    PatientSpecialtyAccessRetrieveUpdateDestroyView,
)

urlpatterns = [
    path("login/", LoginPatientView.as_view(), name="login-patient"),
    path(
        "complete-register/",
        CompletePatientRegistrationView.as_view(),
        name="complete-register-patient",
    ),
    path("me/", PatientProfileView.as_view(), name="view-update-patient-profile"),
    path(
        "specialties/access/",
        PatientSpecialtyAccessListCreateView.as_view(),
        name="patient-specialty-access-list-create",
    ),
    path(
        "specialties/access/<int:pk>/",
        PatientSpecialtyAccessRetrieveUpdateDestroyView.as_view(),
        name="patient-specialty-access-retrieve-update-destroy",
    ),
]
