from django.utils.translation import gettext_lazy as _

from rest_framework import permissions

from doctors.models import Doctor

from .models import CustomUser as User


class HasRole(permissions.BasePermission):
    """
    Permission class that restricts access to users with one or more specific roles.

    To use, define the attribute `required_roles` on your view class,
    setting it to a list or iterable of allowed roles (e.g., `[User.Role.PATIENT, User.Role.DOCTOR]`).
    """

    def _get_required_roles(self, view):
        if hasattr(view, "required_roles"):
            return view.required_roles
        return view.get_required_roles()


    def has_permission(self, request, view):
        user = request.user
        required_roles = self._get_required_roles(view)

        if user.role not in required_roles:
            self.message = _("You don't have the required role.")
            return False

        if not hasattr(user, "patient") and user.role == User.Role.PATIENT:
            self.message = _("Patient profile incomplete.")
            return False

        if user.role == User.Role.DOCTOR:
            if not hasattr(user, "doctor"):
                self.message = _("Doctor profile incomplete.")
                return False
            doctor = user.doctor
            if not hasattr(doctor, "clinic"):
                self.message = _("Doctor clinic incomplete.")
                return False
            if doctor.status == Doctor.Status.PENDING:
                self.message = _(
                    "Your account is under review. Please wait for approval."
                )
                return False
            if doctor.status == Doctor.Status.DECLINED:
                self.message = _(
                    "Your account has been declined. Please contact support for more information."
                )
                return False

        if not hasattr(user, "assistant") and user.role == User.Role.ASSISTANT:
            self.message = _("Assistant profile incomplete.")
            return False

        return True
