from django.contrib import admin

from nested_admin import nested

from .models import Clinic, ClinicImage


class ClinicImageInline(nested.NestedTabularInline):
    model = ClinicImage
    raw_id_fields = ["clinic"]


@admin.register(Clinic)
class ClinicAdmin(nested.NestedModelAdmin):
    list_display = ["doctor", "location", "phone", "time_slot_per_patient"]
    search_fields = ["phone"]
    inlines = [ClinicImageInline]
