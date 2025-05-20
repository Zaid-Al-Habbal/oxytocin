from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from users.models import CustomUser as User
from users.permissions import HasRole

from .serializers import ClinicSerializer


class ClinicCreateView(generics.CreateAPIView):
    serializer_class = ClinicSerializer
    permission_classes = [IsAuthenticated]


class ClinicRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    serializer_class = ClinicSerializer
    permission_classes = [IsAuthenticated, HasRole]
    required_roles = [User.Role.DOCTOR]

    def get_object(self):
        return self.request.user.doctor.clinic
