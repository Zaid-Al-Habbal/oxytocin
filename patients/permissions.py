from django.utils.translation import gettext_lazy as _

from rest_framework.permissions import BasePermission
from clinics.models import BannedPatient

class NotBannedPatient(BasePermission):
    """
    Allows access only if the patient is not banned from the clinic.
    """

    def has_permission(self, request, view):
        # Check if authenticated user is a patient
        user = request.user
        # Retrieve the clinic_id from the request (assume from view.kwargs or request.data)
        clinic_id = (
            view.kwargs.get('clinic_id') or
            request.data.get('clinic') or
            request.query_params.get('clinic')
        )

        if not clinic_id:
            return False  # Cannot verify without clinic ID

        if BannedPatient.objects.filter(patient=user.patient,clinic_id=clinic_id).exists():
            self.message = _("You are banned from this clinic")
            return False
        return True
