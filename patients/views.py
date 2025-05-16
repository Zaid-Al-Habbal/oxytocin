from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.throttling import ScopedRateThrottle
from rest_framework import generics, permissions

from .serializers import LoginPatientSerializer, PatientProfileSerializer, CompletePatientRegistrationSerializer
from .models import Patient
from users.permissions import HasRole
from users.models import CustomUser as User


class LoginPatientView(generics.GenericAPIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'login'

    def post(self, request):
        serializer = LoginPatientSerializer(data=request.data)
        if serializer.is_valid():
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CompletePatientRegistrationView(generics.CreateAPIView):
    serializer_class = CompletePatientRegistrationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Patient.objects.none()
    
    
class PatientProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = PatientProfileSerializer
    required_roles = [User.Role.PATIENT]
    permission_classes = [permissions.IsAuthenticated, HasRole]

    def get_object(self):
        return self.request.user.patient