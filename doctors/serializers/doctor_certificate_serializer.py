from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from file_validator.models import DjangoFileValidator

from users.models import CustomUser as User


class DoctorCertificateSerializer(serializers.Serializer):
    certificate = serializers.FileField(
        validators=[
            DjangoFileValidator(
                libraries=["python_magic", "filetype"],
                acceptable_mimes=[
                    "application/pdf",
                    "image/jpg",
                    "image/jpeg",
                    "image/png",
                    "image/gif",
                    "image/webp",
                    "image/bmp",
                ],
                acceptable_types=["archive", "image"],
                max_upload_file_size=8 * 1024 * 1024,  # 8MB
            )
        ],
        write_only=True,
        help_text="Accepted MIME types: application/pdf, image/jpg, image/jpeg, image/png, image/gif, image/webp, image/bmp. Max file size: 8MB.",
    )
    message = serializers.CharField(read_only=True)

    @property
    def request(self):
        return self.context.get("request")

    @property
    def user(self):
        return self.request.user

    def validate(self, data):
        if self.user.role != User.Role.DOCTOR:
            raise PermissionDenied(_("You don't have the required role."))
        if not hasattr(self.user, "doctor"):
            raise serializers.ValidationError(
                _("Please create a doctor profile first.")
            )
        certificate = self.user.doctor.certificate
        if certificate:
            raise serializers.ValidationError(
                _("A certificate has already been uploaded for this doctor profile.")
            )
        return data

    def create(self, validated_data):
        certificate = validated_data.pop("certificate")
        doctor = self.user.doctor
        doctor.certificate = certificate
        doctor.save()
        return {"message": _("Doctor's certificate uploaded successfully.")}
