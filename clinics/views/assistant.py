from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from clinics.serializers import (
    AddAssistantSerializer,
    ListAssistantsSerializer,
)

from assistants.serializers import AssistantProfileSerializer
from assistants.models import Assistant

from users.models import CustomUser as User
from users.permissions import HasRole


from drf_spectacular.utils import extend_schema, OpenApiExample, extend_schema_view


@extend_schema(
    summary="Add Assistant to Clinic",
    description="Add an Assistant by its phone number to clinic if she is not connected to a clinic.",
    tags=["Assistant Management"],
)
class AddAssistantView(generics.GenericAPIView):
    required_roles = [User.Role.DOCTOR]
    permission_classes = [IsAuthenticated, HasRole]
    serializer_class = AddAssistantSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        assistant = serializer.context["assistant"]
        clinic = request.user.doctor.clinic

        assistant.clinic = clinic
        assistant.joined_clinic_at = timezone.now().date()
        assistant.save()

        return Response(
            {"detail": _("Assistant added successfully!")}, status=status.HTTP_200_OK
        )


@extend_schema(
    summary="List All Assistants in my Clinic",
    description="List assistants basic info that work in my clinic.",
    tags=["Assistant Management"],
)
class ListAssistantView(generics.ListAPIView):
    required_roles = [User.Role.DOCTOR]
    permission_classes = [IsAuthenticated, HasRole]
    serializer_class = ListAssistantsSerializer

    def get_queryset(self):
        return self.request.user.doctor.clinic.assistants.all()


@extend_schema(
    summary="Show Assistant Profile that works in my Clinic",
    description="View all info about the assistant",
    tags=["Assistant Management"],
)
class RetrieveAssistantView(generics.RetrieveAPIView):
    required_roles = [User.Role.DOCTOR]
    permission_classes = [IsAuthenticated, HasRole]
    serializer_class = AssistantProfileSerializer

    def get_queryset(self):
        return self.request.user.doctor.clinic.assistants.all()


@extend_schema(
    summary="Remove Assistant",
    description="Remove assistant that works in my clinic",
    methods=["delete"],
    responses={200},
    examples=[
        OpenApiExample(
            name="Remove Assistant",
            value={"detail": _("Assistant removed from clinic.")},
            response_only=True
        )
    ],
    tags=["Assistant Management"],
)
class RemoveAssistantFromClinic(APIView):
    required_roles = [User.Role.DOCTOR]
    permission_classes = [IsAuthenticated, HasRole]

    def delete(self, request, pk):
        clinic = request.user.doctor.clinic
        try:
            assistant = Assistant.objects.get(user=pk, clinic=clinic)
        except Assistant.DoesNotExist:
            return Response(
                {"detail": _("Assistant not found or not in your clinic.")}, status=404
            )

        assistant.clinic = None
        assistant.joined_clinic_at = None
        assistant.save()

        return Response(
            {"detail": _("Assistant removed from clinic.")}, status=status.HTTP_200_OK
        )
