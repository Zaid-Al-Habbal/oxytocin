from django.urls import path, include

from .views import (
    DoctorLoginView,
    DoctorCreateView,
    DoctorCertificateView,
    DoctorRetrieveUpdateView,
    SpecialtyListView,
    SubspecialtySearchListView,
    DoctorNewestListView,
    DoctorSearchListView,
    DoctorMultiSearchListView,
    DoctorDetailRetrieveView,
)

urlpatterns = [
    path("clinics/", include("clinics.urls")),
    path("login/", DoctorLoginView.as_view(), name="doctor-login"),
    path("", DoctorCreateView.as_view(), name="doctor-create"),
    path("certificates/", DoctorCertificateView.as_view(), name="doctor-certificate"),
    path(
        "my-profile/",
        DoctorRetrieveUpdateView.as_view(),
        name="doctor-retrieve-update",
    ),
    path("specialties/", SpecialtyListView.as_view(), name="specialty-list"),
    path("specialties/<int:pk>/", SubspecialtySearchListView.as_view(), name="specialty-search-list"),
    path("newest/", DoctorNewestListView.as_view(), name="doctor-newest-list"),
    path("search/", DoctorSearchListView.as_view(), name="doctor-search"),
    path("multi-search/", DoctorMultiSearchListView.as_view(), name="doctor-multi-search"),
    path("<int:pk>/", DoctorDetailRetrieveView.as_view(), name="doctor-detail-retrieve"),
]
