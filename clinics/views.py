from rest_framework import generics, mixins
from rest_framework.permissions import IsAuthenticated

from users.models import CustomUser as User
from users.permissions import HasRole

from .models import Clinic, ClinicImage
from .serializers import (
    ClinicSerializer,
    ClinicImageCreateSerializer,
    ClinicImagesUpdateSerializer,
    ClinicImageDeleteSerializer,
)


class ClinicCreateView(generics.CreateAPIView):
    serializer_class = ClinicSerializer
    permission_classes = [IsAuthenticated]


class ClinicRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    queryset = Clinic.objects.all()
    serializer_class = ClinicSerializer
    permission_classes = [IsAuthenticated, HasRole]
    required_roles = [User.Role.DOCTOR]

    def get_object(self):
        return self.request.user.doctor.clinic


class ClinicImageView(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    generics.GenericAPIView,
):
    queryset = ClinicImage.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ClinicImageCreateSerializer
        elif self.request.method == "PUT":
            return ClinicImagesUpdateSerializer
        elif self.request.method == "DELETE":
            return ClinicImageDeleteSerializer
        else:
            return super().get_serializer_class()

    def get_object(self):
        user = self.request.user
        if not hasattr(user, "doctor") or not hasattr(user.doctor, "clinic"):
            return None
        else:
            return user.doctor.clinic

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

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
