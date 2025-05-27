from django.utils.translation import gettext_lazy as _
from django.utils.timezone import now

from rest_framework import status
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import extend_schema, OpenApiExample

from .models import CustomUser as User
from .serializers import (
    UserCreateSerializer,
    LogoutSerializer,
    ChangePasswordSerializer,
)


@extend_schema(
    summary="Register a new user",
    description="Creates a new user account. The password must satisfy the password policy.",
    request=UserCreateSerializer,
    responses={201: UserCreateSerializer},
    examples=[
        OpenApiExample(
            name="User registration example",
            value={
                "first_name": "John",
                "last_name": "Doe",
                "phone": "0999888777",
                "email": "john@example.com",
                "gender": "male",
                "birth_date": "1990-01-01",
                "password": "abcX123#",
                "password_confirm": "abcX123#",
            },
            request_only=True,
        )
    ],
)
class UserCreateDestroyView(generics.CreateAPIView, generics.DestroyAPIView):
    serializer_class = UserCreateSerializer

    def get_object(self):
        return self.request.user

    def get_permissions(self):
        if self.request.method == "DELETE":
            return [permissions.IsAuthenticated()]
        return super().get_permissions()

    def get_queryset(self):
        if self.request.method == "POST":
            return User.objects.all()
        elif self.request.method == "DELETE":
            return User.objects.filter(deleted_at__isnull=True)
        return super().get_queryset()

    def perform_destroy(self, instance):
        if instance.role == User.Role.DOCTOR:
            instance.deleted_at = now()
            instance.save()
        else:
            instance.delete()


class LogoutView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = LogoutSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        refresh_token = serializer.validated_data["refresh"]
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(
                {"detail": _("Logout successful.")},
                status=status.HTTP_205_RESET_CONTENT,
            )
        except TokenError:
            return Response(
                {"error": "Invalid or expired token."},
                status=status.HTTP_400_BAD_REQUEST,
            )


class CustomTokenRefreshView(TokenRefreshView):
    """
    Custom view to refresh tokens with rotation and blacklist support.
    """

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except TokenError:
            return Response(
                {"error": "Invalid or expired token."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class ChangePasswordView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ChangePasswordSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"detail": "Password updated successfully."}, status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
