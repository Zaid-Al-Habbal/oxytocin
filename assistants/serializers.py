from django.utils.translation import gettext as _
from django.contrib.auth import authenticate

from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from users.serializers import UserUpdateSerializer, UserNestedSerializer
from users.models import CustomUser as User

from .models import Assistant


class LoginAssistantSerializer(serializers.Serializer):
    phone = serializers.CharField(write_only=True)
    password = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
        help_text="Password must meet the validation rules (min length=8, has both lowercase and uppercase latters, number, special character, not common, not similar to user's attributes ).",
    )
    access_token = serializers.CharField(read_only=True)
    refresh_token = serializers.CharField(read_only=True)
    
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
        
        

class CompleteAssistantRegistrationSerializer(serializers.ModelSerializer):
    user = UserNestedSerializer()
    
    class Meta:
        model = Assistant
        fields = [
            'user',
            'about',
            'education',
            'start_work_date'
        ] 

    def validate(self, data):
        user = self.context['request'].user
        if not user.is_verified_phone:
            raise serializers.ValidationError(_("Phone number is not verified."))
        if hasattr(user, 'assistant'):
            raise serializers.ValidationError(_("Assistant profile already exists."))
        if user.role != User.Role.ASSISTANT:
            raise serializers.ValidationError(_("You have no access to complete this registration"))
        return data

    def create(self, validated_data):
        user = self.context['request'].user
        user_data = validated_data.pop('user')
        
        user_serializer = UserNestedSerializer(user, data=user_data, partial=True)
        user_serializer.is_valid(raise_exception=True)
        user_serializer.save()

        
        return Assistant.objects.create(user=user, **validated_data)
    
    
class AssistantProfileSerializer(serializers.ModelSerializer):
    user = UserUpdateSerializer()
    class Meta:
        model = Assistant
        fields = [
            'user',
            'about',
            'education',
            'start_work_date'
        ]
    
    def update(self, instance, validated_data):
        user_data = validated_data.pop('user')
        instance = super().update(instance, validated_data)

        user = instance.user
        
        user_serializer = UserUpdateSerializer(user, data=user_data, partial=True)
        user_serializer.is_valid(raise_exception=True)
        user_serializer.save()

        return instance