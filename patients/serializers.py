from django.utils.translation import gettext as _
from django.contrib.auth import authenticate

from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Patient
from users.serializers import UserCreateSerializer, UserUpdateDestroySerializer, UserNestedSerializer
from users.models import CustomUser as User


class LoginPatientSerializer(serializers.Serializer):
    phone = serializers.CharField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, data):
        phone = data.get('phone')
        password = data.get('password')

        user = authenticate(phone=phone, password=password)

        if user is None:
            raise serializers.ValidationError(_("Invalid credentials"))
        
        if user.role != 'patient':
            raise serializers.ValidationError(_("Only patients can log in here."))
        
        if not user.is_verified_phone:
            raise serializers.ValidationError(_("Please, verify your phone number first"))

        refresh = RefreshToken.for_user(user)

        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }


class CompletePatientRegistrationSerializer(serializers.ModelSerializer):
    user = UserNestedSerializer()
    
    class Meta:
        model = Patient
        fields = [
            'user',
            'location',
            'longitude',
            'latitude',
            'job',
            'blood_type',
            'medical_history',
            'surgical_history',
            'allergies',
            'medicines',
            'is_smoker',
            'is_drinker',
            'is_married'
        ] 

    def validate(self, data):
        user = self.context['request'].user
        if not user.is_verified_phone:
            raise serializers.ValidationError(_("Phone number is not verified."))
        if hasattr(user, 'patient'):
            raise serializers.ValidationError(_("Patient profile already exists."))
        if user.role != User.Role.PATIENT:
            raise serializers.ValidationError(_("You have no access to complete this registration"))
        return data

    def create(self, validated_data):
        user = self.context['request'].user
        user_data = validated_data.pop('user')
        
        user_serializer = UserNestedSerializer(user, data=user_data, partial=True)
        user_serializer.is_valid(raise_exception=True)
        user_serializer.save()

        
        return Patient.objects.create(user=user, **validated_data)
    
    
class PatientProfileSerializer(serializers.ModelSerializer):
    user = UserUpdateDestroySerializer()
    class Meta:
        model = Patient
        fields = [
            'user',
            'location',
            'longitude',
            'latitude',
            'job',
            'blood_type',
            'medical_history',
            'surgical_history',
            'allergies',
            'medicines',
            'is_smoker',
            'is_drinker',
            'is_married'
        ]
    
    def update(self, instance, validated_data):
        user_data = validated_data.pop('user')
        instance = super().update(instance, validated_data)

        user = instance.user
        
        user_serializer = UserUpdateDestroySerializer(user, data=user_data, partial=True)
        user_serializer.is_valid(raise_exception=True)
        user_serializer.save()

        return instance