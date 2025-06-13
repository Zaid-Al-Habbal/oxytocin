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


class SpecialtyFilter(admin.SimpleListFilter):
    title = "Main Specialty"
    parameter_name = "main_specialty"

    def lookups(self, request, model_admin):
        main_specialties = Specialty.objects.main_specialties_only()
        return [
            (main_specialty.id, str(main_specialty))
            for main_specialty in main_specialties
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(main_specialties__id=self.value())
        return queryset


@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display = ["name_en", "name_ar"]
    list_filter = [SpecialtyFilter]
    search_fields = ["name_en", "name_ar"]


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ["title", "description", "doctor", "created_at", "updated_at"]
    list_filter = ["doctor", "created_at", "updated_at"]
