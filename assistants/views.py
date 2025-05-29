from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.throttling import ScopedRateThrottle
from rest_framework import generics, permissions

from drf_spectacular.utils import extend_schema, OpenApiExample

from .serializers import LoginAssistantSerializer

from users.permissions import HasRole
from users.models import CustomUser as User


class LoginAssistantView(generics.GenericAPIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'login'
    serializer_class = LoginAssistantSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)