from django.contrib import admin
from django.contrib.gis.db import models

import mapwidgets

from .models import Patient


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ["job", "address", "blood_type"]
    list_filter = ["blood_type"]
    search_fields = ["job"]
    formfield_overrides = {
        models.PointField: {"widget": mapwidgets.GoogleMapPointFieldWidget}
    }
