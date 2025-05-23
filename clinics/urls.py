from django.urls import path

from .views import ClinicCreateView, ClinicRetrieveUpdateView, ClinicImageView

urlpatterns = [
    path("clinics/", ClinicCreateView.as_view(), name="clinic-create"),
    path("my-clinic/", ClinicRetrieveUpdateView.as_view(), name="clinic-retrieve-update"),
    path("my-clinic/images/", ClinicImageView.as_view(), name="clinic-images"),
]
