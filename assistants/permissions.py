from django.utils.translation import gettext_lazy as _

from rest_framework import permissions

from assistants.models import Assistant


class IsAssistantAssociatedWithClinic(permissions.BasePermission):
    def has_permission(self, request, view):
        assistant: Assistant = request.user.assistant
        return hasattr(assistant, "clinic") and assistant.clinic
