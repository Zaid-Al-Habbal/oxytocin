from django.urls import path

from .views import LoginPatientView, CompletePatientRegistrationView

urlpatterns = [
    path('login/', LoginPatientView.as_view(), name='login-patient'),
    path('complete-register/', CompletePatientRegistrationView.as_view(), name='complete-register-patient'),
    
]
