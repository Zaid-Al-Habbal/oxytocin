from django.utils.translation import gettext_lazy as _

from rest_framework.permissions import BasePermission
from rest_framework.exceptions import ValidationError

from users.models import CustomUser as User


class IsDoctorWithClinic(BasePermission):
    """
    Allows access only to doctors with a clinic.
    """

    def has_permission(self, request, view):
        user = request.user
        if user.role != User.Role.DOCTOR:
            self.message = _("You don't have the required role.")
            return False
        if not hasattr(user, "doctor"):
            raise ValidationError(
                {"detail": _("Please create a doctor profile first.")}
            )
        if not hasattr(user.doctor, "clinic"):
            raise ValidationError({"detail": _("Please create a clinic first.")})
        return True
