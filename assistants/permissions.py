from django.utils.translation import gettext_lazy as _

from rest_framework.permissions import BasePermission

from users.models import CustomUser as User
from assistants.models import Assistant


class IsAssistantWithClinic(BasePermission):
    """
    Allows access only to assistants with a clinic.
    """

    def has_permission(self, request, view):
        user = request.user
        if user.role != User.Role.ASSISTANT:
            self.message = _("You don't have the required role.")
            return False
        if not hasattr(user, "assistant"):
            self.message = _("Please create an assistant profile first.")
            return False
        if user.assistant.clinic is None:
            self.message = _("Please join a clinic first.")
            return False
        return True


class IsAssistantAssociatedWithClinic(BasePermission):
    def has_permission(self, request, view):
        assistant: Assistant = request.user.assistant
        return hasattr(assistant, "clinic") and assistant.clinic
