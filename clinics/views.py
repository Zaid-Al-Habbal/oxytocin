from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from rest_framework import generics, mixins, status, serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiExample, inline_serializer

from .models import Clinic, ClinicImage
from .serializers import (
    ClinicSerializer,
    ClinicImageCreateSerializer,
    ClinicImagesUpdateSerializer,
    ClinicImageDeleteSerializer,
    AddAssistantSerializer,
    ListAssistantsSerializer,
)
from doctors.permissions import IsDoctorWithClinic

from assistants.serializers import AssistantProfileSerializer
from assistants.models import Assistant

from users.models import CustomUser as User
from users.permissions import HasRole

@extend_schema(
    summary="Create a Clinic",
    description="Create a clinic for the currently authenticated doctor.",
    tags=["Clinic"],
)
class ClinicCreateView(generics.CreateAPIView):
    serializer_class = ClinicSerializer
    permission_classes = [IsAuthenticated]


@extend_schema_view(
    get=extend_schema(
        summary="Retrieve Clinic",
        description="Returns the clinic data of the currently authenticated doctor.",
        tags=["Clinic"],
    ),
    put=extend_schema(
        summary="Update Clinic",
        description="Updates the clinic data of the currently authenticated doctor.",
        tags=["Clinic"],
    ),
    patch=extend_schema(
        summary="Partial Clinic Update",
        description="Partially updates the clinic data of the currently authenticated doctor. Only the provided fields will be updated.",
        tags=["Clinic"],
    ),
)
class ClinicRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    queryset = Clinic.objects.all()
    serializer_class = ClinicSerializer
    permission_classes = [IsAuthenticated, IsDoctorWithClinic]

    def get_object(self):
        return self.request.user.doctor.clinic


class ClinicImageView(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    generics.GenericAPIView,
):
    queryset = ClinicImage.objects.all()
    permission_classes = [IsAuthenticated, IsDoctorWithClinic]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ClinicImageCreateSerializer
        if self.request.method == "PUT":
            return ClinicImagesUpdateSerializer
        if self.request.method == "DELETE":
            return ClinicImageDeleteSerializer
        return super().get_serializer_class()

    def get_object(self):
        return self.request.user.doctor.clinic

    def get_parsers(self):
        if hasattr(self.request, "method") and self.request.method in ["POST", "PUT"]:
            return [MultiPartParser()]
        return super().get_parsers()

    @extend_schema(
        summary="Upload one or more Clinic Image",
        description="Upload one or more clinic image to the clinic of the currently authenticated doctor.",
        examples=[
            OpenApiExample(
                name="Upload clinic images",
                value={
                    "images[0]": "image.jpg",
                    "images[1]": "image.jpeg",
                    "images[2]": "image.png",
                    "images[3]": "image.gif",
                    "images[4]": "image.webp",
                    "images[5]": "image.bmp",
                },
                request_only=True,
                media_type="multipart/form-data",
            )
        ],
        tags=["Clinic Images"],
    )
    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    @extend_schema(
        summary="Edit one or more Clinic Image",
        description="Edit one or more clinic image to the clinic of the currently authenticated doctor.",
        examples=[
            OpenApiExample(
                name="Edit clinic images",
                value={
                    "clinic_images[0]id": 1,
                    "clinic_images[0]image": "image.png",
                    "clinic_images[1]id": 2,
                    "clinic_images[1]image": "image2.png",
                },
                request_only=True,
                media_type="multipart/form-data",
            )
        ],
        tags=["Clinic Images"],
    )
    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    @extend_schema(
        summary="Delete one or more Clinic Image",
        description="""
        Delete one or more clinic image to the clinic of the currently authenticated doctor.

        Payload Example:
            Content type: application/json
            {
                "clinic_images": [1, 2, 3, 4, 5]    # length <= 8, duplicates not allowed
            }
        """,
        request=ClinicImageDeleteSerializer,
        examples=[
            OpenApiExample(
                name="Delete clinic images",
                value={
                    "clinic_images": [1, 2, 3, 4, 5],
                },
                request_only=True,
            )
        ],
        tags=["Clinic Images"],
    )
    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)

    def perform_destroy(self, instance):
        serializer = self.get_serializer(
            data=self.request.data, context={"request": self.request}
        )
        serializer.is_valid(raise_exception=True)
        clinic_images = serializer.validated_data.get("clinic_images")
        for clinic_image in clinic_images:
            clinic_image.delete()


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
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        assistant = serializer.context["assistant"]
        clinic = request.user.doctor.clinic

        assistant.clinic = clinic
        assistant.joined_clinic_at = timezone.now().date()
        assistant.save()

        return Response({"detail": _("Assistant added successfully!")}, status=status.HTTP_200_OK)
    
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
class RetriveAssistantView(generics.RetrieveAPIView):
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
            name="Leave My clinic",
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
            return Response({"detail": _("Assistant not found or not in your clinic.")}, status=404)
        
        assistant.clinic = None
        assistant.joined_clinic_at = None
        assistant.save()
        
        return Response({"detail": _("Assistant removed from clinic.")}, status=status.HTTP_200_OK)
        