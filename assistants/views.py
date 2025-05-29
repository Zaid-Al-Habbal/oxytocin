from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.throttling import ScopedRateThrottle
from rest_framework import generics, permissions

from drf_spectacular.utils import extend_schema, OpenApiExample

from .serializers import LoginAssistantSerializer, CompleteAssistantRegistrationSerializer
from .models import Assistant

from users.permissions import HasRole
from users.models import CustomUser as User


@extend_schema(
    summary="Assistant Login",
    description="Authenticate a Assistant using phone and password. Returns access credentials if successful.",
    tags=["Assistant"],
)
class LoginAssistantView(generics.GenericAPIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'login'
    serializer_class = LoginAssistantSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)
    
@extend_schema(
    summary="Complete Assistant registeration",
    description="Creates a new Assistant profile",
    request=CompleteAssistantRegistrationSerializer,
    responses={201: CompleteAssistantRegistrationSerializer},
    examples=[
        OpenApiExample(
            name="Complete Assistant registeration example",
            value={   
                "user": {
                    "gender": "male",
                    "birth_date": "2004-9-30"
                },
                "about": "worked in two previous clinics",
                "education": "Bachalor of Management",
                "start_work_date": "2020-2-2"
            },
            request_only=True,
        )
    ],
    tags=["Assistant"],
)
class CompleteAssistantRegistrationView(generics.CreateAPIView):
    serializer_class = CompleteAssistantRegistrationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Assistant.objects.none()