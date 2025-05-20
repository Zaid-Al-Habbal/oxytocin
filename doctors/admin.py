from django.contrib import admin

from nested_admin import nested

from clinics.models import Clinic
from clinics.admin import ClinicImageInline

from .models import Doctor, Specialty, DoctorSpecialty, Achievement


class DoctorSpecialtyInline(nested.NestedTabularInline):
    model = DoctorSpecialty
    autocomplete_fields = ["specialty"]


class ClinicInline(nested.NestedTabularInline):
    model = Clinic
    extra = 1
    inlines = [ClinicImageInline]


@admin.register(Doctor)
class DoctorAdmin(nested.NestedModelAdmin):
    list_display = [
        "user",
        "about",
        "education",
        "start_work_date",
        "status",
        "certificate",
    ]
    list_filter = ["status"]
    list_editable = ["status"]
    inlines = [DoctorSpecialtyInline, ClinicInline]


@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display = ["name", "parent"]
    list_filter = ["parent"]
    search_fields = ["name"]


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ["title", "description", "doctor", "created_at", "updated_at"]
    list_filter = ["doctor", "created_at", "updated_at"]
