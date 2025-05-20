from django.urls import path, include

from .views import DoctorLoginView, DoctorCreateView, DoctorRetrieveUpdateView

urlpatterns = [
    path("", include("clinics.urls")),
    path("login/", DoctorLoginView.as_view(), name="doctor-login"),
    path("", DoctorCreateView.as_view(), name="doctor-create"),
    path("my-profile/", DoctorRetrieveUpdateView.as_view(), name="doctor-retrieve-update"),
]
