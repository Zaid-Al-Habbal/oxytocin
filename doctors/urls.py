from django.urls import path, include

from .views import (
    DoctorLoginView,
    DoctorCreateView,
    DoctorCertificateView,
    DoctorRetrieveUpdateView,
    SpecialtyListView,
)

urlpatterns = [
    path("", include("clinics.urls")),
    path("login/", DoctorLoginView.as_view(), name="doctor-login"),
    path("", DoctorCreateView.as_view(), name="doctor-create"),
    path("certificates/", DoctorCertificateView.as_view(), name="doctor-certificate"),
    path(
        "my-profile/",
        DoctorRetrieveUpdateView.as_view(),
        name="doctor-retrieve-update",
    ),
    path("specialties/", SpecialtyListView.as_view(), name="specialty-list"),
]
