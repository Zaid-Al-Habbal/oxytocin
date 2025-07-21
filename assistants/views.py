from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.throttling import ScopedRateThrottle
from rest_framework import generics, permissions

from drf_spectacular.utils import extend_schema, OpenApiExample, extend_schema_view, inline_serializer

from .serializers import LoginAssistantSerializer, CompleteAssistantRegistrationSerializer, AssistantProfileSerializer
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
    
    
@extend_schema_view(
    get=extend_schema(
        summary="Retrieve Assistant Profile",
        description="Returns the profile data of the currently authenticated Assistant.",
        tags=["Assistant"],
    ),
    patch=extend_schema(
        summary="Update Assistant Profile",
        description="Updates the profile data of the currently authenticated Assistant.",
        tags=["Assistant"],
    )
)
class AssistantProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = AssistantProfileSerializer
    required_roles = [User.Role.ASSISTANT]
    permission_classes = [permissions.IsAuthenticated, HasRole]
    http_method_names = ["get", "patch"]

    def get_object(self):
        return self.request.user.assistant
    
@extend_schema(
    summary="Assistant leave his/her clinic",
    description="Assitant can use this endpoint to leave its clinic if he/she is connected to one",
    methods=["delete"],
    responses={200},
    examples=[
        OpenApiExample(
            name="Leave My clinic",
            value={"detail": _("You leaved your clinic.")},
            response_only=True
        )
    ],
    tags=["Assistant"]
)
class LeaveMyClinicView(APIView):
    required_roles = [User.Role.ASSISTANT]
    permission_classes = [permissions.IsAuthenticated, HasRole]
    
    def delete(self, request):
        assistant = request.user.assistant
        
        if assistant.clinic is None:
            return Response({"detail": _("You are not connected to any clinic.")}, status=status.HTTP_404_NOT_FOUND)
        
        assistant.clinic = None
        assistant.joined_clinic_at = None
        assistant.save()
        
        return Response({"detail": _("You leaved your clinic.")}, status=status.HTTP_200_OK)
    