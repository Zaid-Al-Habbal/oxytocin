from django.contrib import admin
from django.contrib.gis.db import models

import mapwidgets
from nested_admin import nested

from .models import Clinic, ClinicImage


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
