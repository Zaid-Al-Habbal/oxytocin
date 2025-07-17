from django.urls import path

from .views import *

urlpatterns = [
    path('<int:clinic_id>/visit-times/', ClinicVisitTimesView.as_view(), name='list-clinic-visit-times'),
    path('<int:clinic_id>/book/', BookAppointmentView.as_view(), name='book-appointment'),
    path('<int:appointment_id>/cancel/', CancelAppointmentView.as_view(), name='cancel-appointment'),
    path('', ShowMyAppointmentsView.as_view(), name='show-my-appointments'),
    path('<int:appointment_id>/rebook/', RebookAppointmentView.as_view(), name='rebook-appointment'),
    path('<int:appointment_id>/update/', UpdateAppointmentView.as_view(), name='update-appointment'),
    path('my-clinic/', MyClinicAppointmentsView.as_view(), name='list-my-clinic-appointments'),
    path('my-clinic/<int:appointment_id>/', AppointmentDetailView.as_view(), name='show-my-clinic-appointment-in-detail'),
    path('my-clinic/<int:appointment_id>/change-status/', ChangeAppointmentStatusView.as_view(), name='change-appointment-status'),
    path('<int:appointment_id>/upload-attachments/', AppointmentAttachmentUploadView.as_view(), name='upload-attachments'),
    
]
