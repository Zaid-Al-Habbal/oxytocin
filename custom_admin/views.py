from django.shortcuts import render
from custom_admin.admin import (
    PatientsLineComponent,
    DoctorsLineComponent,
    AssistantsLineComponent,
)


def dashboard_callback(request, context):
    context.update(
        {
            "patients_count": PatientsLineComponent(request).get_count(),
            "doctors_count": DoctorsLineComponent(request).get_count(),
            "assistants_count": AssistantsLineComponent(request).get_count(),
        }
    )

    return context
