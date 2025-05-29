from django.utils.translation import gettext as _
from django.contrib.auth import authenticate

from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from users.serializers import UserUpdateSerializer, UserNestedSerializer
from users.models import CustomUser as User


class LoginAssistantSerializer(serializers.Serializer):
    phone = serializers.CharField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, data):
        phone = data.get('phone')
        password = data.get('password')

        user = authenticate(phone=phone, password=password)

        if user is None:
            raise serializers.ValidationError(_("Invalid credentials"))
        
        if user.role != 'assistant':
            raise serializers.ValidationError(_("Only assistants can log in here."))
        
        if not user.is_verified_phone:
            raise serializers.ValidationError(_("Please, verify your phone number first"))

        refresh = RefreshToken.for_user(user)

        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }