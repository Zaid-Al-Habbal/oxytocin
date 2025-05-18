from django.urls import path

from . import views

urlpatterns = [
    path("login/", views.DoctorLoginView.as_view(), name="doctor-login"),
    path("register/", views.DoctorCreateView.as_view(), name="doctor-create"),
    path("<int:pk>/", views.DoctorRetrieveUpdateView.as_view(), name="doctor-retrieve-update"),
]
