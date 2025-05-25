from rest_framework import status
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import ScopedRateThrottle

from .models import Doctor
from users.models import CustomUser as User
from users.permissions import HasRole
from .serializers import (
    DoctorLoginSerializer,
    DoctorCreateSerializer,
    DoctorUpdateSerializer,
)


class DoctorLoginView(generics.GenericAPIView):
    serializer_class = DoctorLoginSerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class DoctorCreateView(generics.CreateAPIView):
    serializer_class = DoctorCreateSerializer
    permission_classes = [IsAuthenticated]


class DoctorRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    queryset = Doctor.objects.filter(user__deleted_at__isnull=True)
    serializer_class = DoctorUpdateSerializer
    permission_classes = [IsAuthenticated, HasRole]
    required_roles = [User.Role.DOCTOR]
    http_method_names = ["get", "put"]

    def get_object(self):
        return self.request.user.doctor
