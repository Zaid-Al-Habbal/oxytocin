from django.urls import path

from .views import ClinicCreateView, ClinicRetrieveUpdateView

urlpatterns = [
    path("clinics/", ClinicCreateView.as_view(), name="clinic-create"),
    path("my-clinic/", ClinicRetrieveUpdateView.as_view(), name="clinic-retrieve-update"),
]
