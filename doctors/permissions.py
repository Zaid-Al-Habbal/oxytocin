from django.utils.translation import gettext_lazy as _

from rest_framework.permissions import BasePermission

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
            self.message = _("Please create a doctor profile first.")
            return False
        certificate = user.doctor.certificate
        if not certificate:
            self.message = _("Please upload a certificate first.")
            return False
        if not hasattr(user.doctor, "clinic"):
            self.message = _("Please create a clinic first.")
            return False
        return True
