from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field

from doctors.models import Doctor, Specialty, DoctorSpecialty
from users.serializers import (
    UserSerializer,
    UserSummarySerializer,
    UserDetailSerializer,
)

from .specialty import SpecialtySerializer


class DoctorSpecialtySerializer(serializers.ModelSerializer):
    specialty_id = serializers.PrimaryKeyRelatedField(
        queryset=Specialty.objects.with_main_specialties().all(),
        source="specialty",
        write_only=True,
    )
    specialty = SpecialtySerializer(read_only=True)

    class Meta:
        model = DoctorSpecialty
        fields = ["specialty_id", "specialty", "university", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]


class DoctorSpecialtyDetailSerializer(serializers.ModelSerializer):
    specialty_id = serializers.PrimaryKeyRelatedField(
        queryset=Specialty.objects.with_main_specialties().all(),
        source="specialty",
        write_only=True,
    )
    specialty = SpecialtySerializer(read_only=True)

    class Meta:
        model = DoctorSpecialty
        fields = ["specialty_id", "specialty", "university"]


class DoctorSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    main_specialty = DoctorSpecialtySerializer(read_only=True)
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

    def validate_subspecialties(self, value):
        doctor = self.instance
        main_specialty = doctor.main_specialties[0].specialty
        valid_subspecialties_for_main = set(main_specialty.subspecialties.all())
        if len(value) > len(valid_subspecialties_for_main):
            raise serializers.ValidationError(
                _(
                    "You cannot provide more subspecialties than the ones available for the main specialty."
                )
            )
        seen_specialty_pks = set()
        for item in value:
            specialty = item["specialty"]
            if specialty.pk in seen_specialty_pks:
                raise serializers.ValidationError(_("Duplicate is not allowed."))
            seen_specialty_pks.add(specialty.pk)
            if not specialty.main_specialties.exists():
                msg = _('Specialty "%(value)s" - is not a subspecialty.')
                raise serializers.ValidationError(_(msg % {"value": specialty.pk}))
            if not specialty.main_specialties.filter(pk=main_specialty.pk).exists():
                msg = _(
                    'Subspecialty "%(value)s" - is not a branch of the main specialty.'
                )
                raise serializers.ValidationError(_(msg % {"value": specialty.pk}))
        return value

    def to_representation(self, instance):
        instance.main_specialty = instance.main_specialties[0]
        return super().to_representation(instance)

    def update(self, instance, validated_data):
        user_data = validated_data.pop("user")
        subspecialties_data = validated_data.pop("subspecialties")

        user = instance.user
        user_serializer = UserSerializer(
            instance=user,
            data=user_data,
            partial=True,
        )
        user_serializer.is_valid(raise_exception=True)
        user_serializer.save()

        instance.about = validated_data.get("about", instance.about)
        instance.education = validated_data.get("education", instance.education)
        instance.start_work_date = validated_data.get(
            "start_work_date", instance.start_work_date
        )
        instance.save()

        current_subspecialties = instance.subspecialties

        current_subspecialties_ids = set(
            [subspecialty.specialty_id for subspecialty in current_subspecialties]
        )
        incoming_subspecialties_ids = set(
            [
                subspecialty_data["specialty"].id
                for subspecialty_data in subspecialties_data
            ]
        )
        subspecialties_to_remove_ids = (
            current_subspecialties_ids - incoming_subspecialties_ids
        )
        if subspecialties_to_remove_ids:
            DoctorSpecialty.objects.filter(
                doctor=instance,
                specialty_id__in=list(subspecialties_to_remove_ids),
            ).delete()

        for subspecialty_data in subspecialties_data:
            specialty = subspecialty_data["specialty"]
            university = subspecialty_data["university"]
            DoctorSpecialty.objects.update_or_create(
                doctor=instance,
                specialty=specialty,
                defaults={"university": university},
            )

        instance = Doctor.objects.with_categorized_specialties().get(pk=instance.pk)
        return instance


class DoctorSummarySerializer(serializers.ModelSerializer):
    user = UserSummarySerializer()
    main_specialty = serializers.SerializerMethodField()

    class Meta:
        model = Doctor
        fields = [
            "user",
            "about",
            "main_specialty",
        ]

    @extend_schema_field(SpecialtySerializer)
    def get_main_specialty(self, obj):
        main_specialty = obj.specialties.main_specialties_only()[0]
        serializer = SpecialtySerializer(main_specialty)
        return serializer.data


class DoctorDetailSerializer(serializers.ModelSerializer):
    user = UserDetailSerializer()
    main_specialty = DoctorSpecialtyDetailSerializer()
    subspecialties = DoctorSpecialtyDetailSerializer(many=True)

    class Meta:
        model = Doctor
        fields = [
            "user",
            "about",
            "education",
            "main_specialty",
            "subspecialties",
        ]

    def to_representation(self, instance):
        instance.main_specialty = instance.main_specialties[0]
        return super().to_representation(instance)
