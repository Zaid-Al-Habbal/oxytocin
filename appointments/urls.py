from django.urls import path

from .views import *

urlpatterns = [
    path('<int:clinic_id>/visit-times/', ClinicVisitTimesView.as_view(), name='list-clinic-visit-times'),
    path('<int:clinic_id>/book/', BookAppointmentView.as_view(), name='book-appointment')
    
]
