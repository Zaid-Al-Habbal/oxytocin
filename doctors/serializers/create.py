from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from users.models import CustomUser as User
from users.serializers import UserNestedSerializer

from doctors.models import Doctor, DoctorSpecialty

from .base import DoctorSpecialtySerializer


class DoctorCreateSerializer(serializers.ModelSerializer):
    user = UserNestedSerializer()
    main_specialty = DoctorSpecialtySerializer()
    subspecialties = DoctorSpecialtySerializer(many=True)

    class Meta:
        model = Doctor
        fields = [
            "user",
            "about",
            "education",
            "start_work_date",
            "status",
            "main_specialty",
            "subspecialties",
        ]
        read_only_fields = ["status"]

    @property
    def request(self):
        return self.context.get("request")

    def validate_main_specialty(self, value):
        specialty = value["specialty"]
        if specialty.main_specialties.exists():
            raise serializers.ValidationError(
                _("Main specialty cannot be a subspecialty.")
            )
        return value

    def validate_subspecialties(self, value):
        seen_specialty_pks = set()
        for item in value:
            specialty = item["specialty"]
            if specialty.pk in seen_specialty_pks:
                raise serializers.ValidationError(_("Duplicate is not allowed."))
            seen_specialty_pks.add(specialty.pk)
        return value

    def validate(self, data):
        user = self.request.user
        if user.role != User.Role.DOCTOR:
            raise PermissionDenied(_("You don't have the required role."))
        if not user.is_verified_phone:
            raise serializers.ValidationError(_("Phone number is not verified."))
        if hasattr(user, "doctor"):
            raise serializers.ValidationError(_("You already have a doctor profile."))

        main_specialty_data = data["main_specialty"]
        subspecialties_data = data["subspecialties"]
        main_specialty = main_specialty_data["specialty"]
        valid_subspecialties_for_main = set(main_specialty.subspecialties.all())
        if len(subspecialties_data) > len(valid_subspecialties_for_main):
            raise serializers.ValidationError(
                _(
                    "You cannot provide more subspecialties than the ones available for the main specialty."
                )
            )
        for subspecialty_data in subspecialties_data:
            specialty = subspecialty_data["specialty"]
            if specialty not in valid_subspecialties_for_main:
                msg = _(
                    'Subspecialty "%(value)s" - is not a branch of the main specialty.'
                )
                raise serializers.ValidationError(_(msg % {"value": specialty.pk}))
        return data

    def to_representation(self, instance):
        instance.main_specialty = instance.main_specialties[0]
        return super().to_representation(instance)

    def create(self, validated_data):
        user_data = validated_data.pop("user")
        main_specialty_data = validated_data.pop("main_specialty")
        subspecialties_data = validated_data.pop("subspecialties")

        user = self.context["request"].user
        user_serializer = UserNestedSerializer(
            instance=user,
            data=user_data,
            partial=True,
        )
        user_serializer.is_valid(raise_exception=True)
        user = user_serializer.save()

        doctor = Doctor.objects.create(user=user, **validated_data)

        main_specialty = main_specialty_data["specialty"]
        university = main_specialty_data["university"]
        specialties = [
            DoctorSpecialty(
                doctor=doctor, specialty=main_specialty, university=university
            )
        ]
        specialties.extend(
            [
                DoctorSpecialty(
                    doctor=doctor,
                    specialty=subspecialty_data["specialty"],
                    university=subspecialty_data["university"],
                )
                for subspecialty_data in subspecialties_data
            ]
        )
        DoctorSpecialty.objects.bulk_create(specialties)
        doctor = Doctor.objects.with_categorized_specialties().get(pk=doctor.pk)
        return doctor
