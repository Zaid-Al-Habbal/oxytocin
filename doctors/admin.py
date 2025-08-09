from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from unfold.contrib.filters.admin import (
    MultipleDropdownFilter,
    ChoicesCheckboxFilter,
)

from .models import (
    Doctor,
    Specialty,
    DoctorSpecialty,
    Achievement,
    MainSpecialtySubspecialty,
)


class DoctorSpecialtyInline(TabularInline):
    model = DoctorSpecialty
    autocomplete_fields = ["specialty"]
    tab = True


@admin.register(Doctor)
class DoctorAdmin(ModelAdmin):
    list_display = [
        "user_id",
        "user",
        "about",
        "education",
        "start_work_date",
        "status",
        "certificate",
    ]
    list_filter_submit = True
    list_filter = [("status", ChoicesCheckboxFilter)]
    list_editable = ["status"]
    inlines = [DoctorSpecialtyInline]


class SpecialtyFilter(MultipleDropdownFilter):
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
            return queryset.filter(main_specialties__id__in=self.value())
        return queryset


class SpecialtyInline(TabularInline):
    fk_name = "main_specialty"
    model = MainSpecialtySubspecialty
    autocomplete_fields = ["subspecialty"]
    tab = True


@admin.register(Specialty)
class SpecialtyAdmin(ModelAdmin):
    list_display = ["id", "name_en", "name_ar"]
    list_filter_submit = True
    list_filter = [SpecialtyFilter]
    search_fields = ["name_en", "name_ar"]
    inlines = [SpecialtyInline]


class AchievementDoctorFilter(admin.SimpleListFilter):
    title = "Doctor"
    parameter_name = "doctor_id"

    def lookups(self, request, model_admin):
        doctors = Doctor.objects.with_user().all()
        return [(doctor.user.id, str(doctor.user)) for doctor in doctors]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(doctor_id=self.value())
        return queryset


@admin.register(Achievement)
class AchievementAdmin(ModelAdmin):
    list_display = ["id", "title", "description", "doctor", "created_at", "updated_at"]
    list_filter = [AchievementDoctorFilter, "created_at", "updated_at"]
    search_fields = ["title", "description"]
    readonly_fields = ["created_at", "updated_at"]
