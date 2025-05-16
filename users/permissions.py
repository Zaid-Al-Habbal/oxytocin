from django.utils.translation import gettext_lazy as _

from rest_framework import permissions

from .models import CustomUser as User


class HasRole(permissions.BasePermission):
    """
    Permission class that restricts access to users with one or more specific roles.

    To use, define the attribute `required_roles` on your view class,
    setting it to a list or iterable of allowed roles (e.g., `[User.Role.PATIENT, User.Role.DOCTOR]`).
    """

    def has_permission(self, request, view):
        user = request.user
        required_roles = view.required_roles

        if user.role not in required_roles:
            self.message = _("You don't have the required role.")
            return False

        if (
            not hasattr(user, User.Role.PATIENT.value)
            and user.role == User.Role.PATIENT.value
        ):
            self.message = _("Patient profile incomplete.")
            return False

        if (
            not hasattr(user, User.Role.DOCTOR.value)
            and user.role == User.Role.DOCTOR.value
        ):
            self.message = _("Doctor profile incomplete.")
            return False

        if (
            not hasattr(user, User.Role.ASSISTANT.value)
            and user.role == User.Role.ASSISTANT.value
        ):
            self.message = _("Assistant profile incomplete.")
            return False

        return True
