from django.urls import path

from .views import LoginPatientView

urlpatterns = [
    path('login/', LoginPatientView.as_view(), name='login-patient'),
]
