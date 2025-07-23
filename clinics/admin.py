from django.contrib import admin
from django.contrib.gis.db import models

import mapwidgets
from nested_admin import nested

from .models import Clinic, ClinicImage, ClinicPatient


class ClinicImageInline(nested.NestedTabularInline):
    model = ClinicImage
    raw_id_fields = ["clinic"]


@admin.register(Clinic)
class ClinicAdmin(nested.NestedModelAdmin):
    list_display = ["doctor", "address", "phone"]
    search_fields = ["phone"]
    inlines = [ClinicImageInline]
    formfield_overrides = {
        models.PointField: {"widget": mapwidgets.GoogleMapPointFieldWidget}
    }


@admin.register(ClinicPatient)
class ClinicPatientAdmin(admin.ModelAdmin):
    list_display = ["clinic", "patient", "cost", "created_at", "updated_at"]
    readonly_fields = ["created_at", "updated_at"]
    search_fields = ["phone"]