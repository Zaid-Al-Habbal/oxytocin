from django.contrib import admin
from django.contrib.gis.db import models

import mapwidgets
from nested_admin import nested

from .models import BannedPatient, Clinic, ClinicImage


class ClinicImageInline(nested.NestedTabularInline):
    model = ClinicImage
    raw_id_fields = ["clinic"]


@admin.register(Clinic)
class ClinicAdmin(nested.NestedModelAdmin):
    list_display = ["doctor_id", "doctor", "address", "phone"]
    search_fields = ["phone"]
    inlines = [ClinicImageInline]
    formfield_overrides = {
        models.PointField: {"widget": mapwidgets.GoogleMapPointFieldWidget}
    }


@admin.register(BannedPatient)
class BannedPatientAdmin(admin.ModelAdmin):
    list_display = ["id", "clinic", "patient", "created_at"]
    readonly_fields = ["created_at"]
    search_fields = ["clinic__phone", "patient__first_name", "patient__last_name"]