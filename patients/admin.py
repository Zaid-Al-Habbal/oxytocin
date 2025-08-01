from django.contrib import admin
from django.contrib.gis.db import models

import mapwidgets

from .models import Patient, PatientSpecialtyAccess


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ["user_id", "job", "address", "blood_type"]
    list_filter = ["blood_type"]
    search_fields = ["job"]
    formfield_overrides = {
        models.PointField: {"widget": mapwidgets.GoogleMapPointFieldWidget}
    }


@admin.register(PatientSpecialtyAccess)
class PatientSpecialtyAccessAdmin(admin.ModelAdmin):
    list_display = ["id", "patient", "specialty", "visibility"]
    list_filter = [
        ("patient__user", admin.RelatedOnlyFieldListFilter),
        ("specialty", admin.RelatedOnlyFieldListFilter),
        "visibility",
    ]
    list_editable = ["visibility"]
    search_fields = [
        "patient__user__first_name",
        "patient__user__last_name",
        "specialty__name_en",
        "specialty__name_ar",
        "visibility",
    ]
    readonly_fields = ["created_at"]
