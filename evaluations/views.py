from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.contrib.auth.models import AnonymousUser

from assistants.models import Assistant
from evaluations.models import Evaluation
from evaluations.serializers import EvaluationSerializer, EvaluationUpdateSerializer

from patients.models import Patient
from users.models import CustomUser as User
from users.permissions import HasRole


class EvaluationPagination(PageNumberPagination):
    page_size = 30
    page_size_query_param = "page_size"
    max_page_size = 50


class EvaluationListCreateView(generics.ListCreateAPIView):
    serializer_class = EvaluationSerializer
    pagination_class = EvaluationPagination

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), HasRole()]
        return super().get_permissions()

    def get_required_roles(self):
        if self.request.method == "POST":
            return [User.Role.PATIENT]
        return [User.Role.DOCTOR, User.Role.PATIENT, User.Role.ASSISTANT]

    def get_queryset(self):
        user: User = self.request.user
        if isinstance(user, AnonymousUser) or user.role == User.Role.PATIENT:
            clinic_id = self.request.query_params.get("clinic_id")
            if clinic_id:
                return Evaluation.objects.latest_per_patient_by_clinic(clinic_id)
        elif user.role == User.Role.DOCTOR:
            return Evaluation.objects.by_clinic(user.pk)
        elif user.role == User.Role.ASSISTANT:
            assistant: Assistant = Assistant.objects.with_clinic().get(user=user)
            return Evaluation.objects.by_clinic(assistant.clinic.pk)
        return Evaluation.objects.none()

    def perform_create(self, serializer):
        patient: Patient = self.request.user.patient
        serializer.save(patient_id=patient.pk)


class EvaluationRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    serializer_class = EvaluationUpdateSerializer
    permission_classes = [IsAuthenticated, HasRole]
    required_roles = [User.Role.PATIENT]

    def get_queryset(self):
        patient: Patient = self.request.user.patient
        qs = Evaluation.objects.filter(patient_id=patient.pk)
        if self.request.method != "GET":
            return qs.within_24_hours()
        return qs
