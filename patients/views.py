from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.throttling import ScopedRateThrottle
from rest_framework import generics, permissions

from drf_spectacular.utils import extend_schema, OpenApiExample

from .serializers import LoginPatientSerializer, PatientProfileSerializer, CompletePatientRegistrationSerializer
from .models import Patient
from users.permissions import HasRole
from users.models import CustomUser as User


class LoginPatientView(generics.GenericAPIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'login'
    serializer_class = LoginPatientSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


@extend_schema(
    summary="Complete Patient registeration",
    description="Creates a new patient profile",
    request=CompletePatientRegistrationSerializer,
    responses={201: CompletePatientRegistrationSerializer},
    examples=[
        OpenApiExample(
            name="Complete Patient registeration example",
            value={   
                "user": {
                    "first_name": "Zaid",
                    "last_name": "Al Habbal", 
                    "gender": "male",
                    "birth_date": "2004-9-30"
                },

                "location": "Maysaat",
                "longitude": 123.42423,
                "latitude": 234.32423,
                "job": "Engineer",
                "blood_type": "B+",
                "medical_history": "",
                "surgical_history": "",
                "medicines": "",
                "allergies": "",
                "is_drinker": False,
                "is_married": False,
                "is_smoker": True
            },
            request_only=True,
        )
    ],
)
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