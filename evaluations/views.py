from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination

from evaluations.models import Evaluation
from evaluations.serializers import EvaluationSerializer

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
        doctor_id = self.request.query_params.get("doctor_id")
        if doctor_id:
            return Evaluation.objects.filter(doctor_id=doctor_id)
        return Evaluation.objects.none()

    def perform_create(self, serializer):
        patient: Patient = self.request.user.patient
        serializer.save(patient_id=patient.pk)


class EvaluationDestroyView(generics.DestroyAPIView):
    serializer_class = EvaluationSerializer
    permission_classes = [IsAuthenticated, HasRole]
    required_roles = [User.Role.PATIENT]

    def get_queryset(self):
        return Evaluation.objects.filter(patient_id=self.request.user.pk)
