from django.utils.translation import gettext_lazy as _

from rest_framework import generics, mixins
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser
from drf_spectacular.utils import extend_schema, OpenApiExample

from clinics.models import ClinicImage
from clinics.serializers import (
    ClinicImageCreateSerializer,
    ClinicImagesUpdateSerializer,
    ClinicImageDeleteSerializer,
)
from doctors.permissions import IsDoctorWithClinic


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
