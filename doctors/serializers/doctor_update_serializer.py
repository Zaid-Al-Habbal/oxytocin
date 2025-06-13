from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from users.serializers import UserUpdateSerializer

from doctors.models import Doctor, DoctorSpecialty

from .doctor_specialty_serializer import DoctorSpecialtySerializer


class DoctorUpdateSerializer(serializers.ModelSerializer):
    user = UserUpdateSerializer()
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
        main_specialty = doctor.main_specialty[0].specialty
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
        main_specialty_data = DoctorSpecialtySerializer(instance.main_specialty[0]).data
        subspecialties_data = DoctorSpecialtySerializer(
            instance.subspecialties,
            many=True,
        ).data
        return {
            "user": UserUpdateSerializer(instance.user).data,
            "about": instance.about,
            "education": instance.education,
            "start_work_date": instance.start_work_date,
            "status": instance.status,
            "main_specialty": main_specialty_data,
            "subspecialties": subspecialties_data,
        }

    def update(self, instance, validated_data):
        user_data = validated_data.pop("user")
        subspecialties_data = validated_data.pop("subspecialties")

        user = instance.user
        user_serializer = UserUpdateSerializer(
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
