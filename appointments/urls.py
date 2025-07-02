from django.urls import path

from .views import *

urlpatterns = [
    path('<int:clinic_id>/visit-times/', ClinicVisitTimesView.as_view(), name='list-clinic-visit-times'),
    path('<int:clinic_id>/book/', BookAppointmentView.as_view(), name='book-appointment'),
    path('<int:appointment_id>/cancel/', CancelAppointmentView.as_view(), name='cancel-appointment'),
    path('', ShowMyAppointmentsView.as_view(), name='show-my-appointments'),
    path('<int:appointment_id>/rebook/', RebookAppointmentView.as_view(), name='rebook-appointment'),
]
