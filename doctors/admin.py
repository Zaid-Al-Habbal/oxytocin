from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy
from django.utils.html import format_html
from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from unfold.contrib.filters.admin import (
    MultipleDropdownFilter,
    ChoicesCheckboxFilter,
)
from import_export.admin import ImportExportModelAdmin
from unfold.contrib.import_export.forms import ImportForm, SelectableFieldsExportForm
from simple_history.admin import SimpleHistoryAdmin

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
class DoctorAdmin(SimpleHistoryAdmin, ModelAdmin, ImportExportModelAdmin):
    import_form_class = ImportForm
    export_form_class = SelectableFieldsExportForm

    list_display = [
        "id",  # This is the user_id
        "user",
        "about",
        "start_work_date",
        "status",
        "certificate_link",
    ]
    search_fields = ["user__first_name", "user__last_name", "user__phone"]
    list_filter_submit = True
    list_filter = [("status", ChoicesCheckboxFilter)]
    list_editable = ["status"]
    inlines = [DoctorSpecialtyInline]

    def certificate_link(self, obj):
        doctor: Doctor = obj
        return format_html(
            '<a href="{}" target="_blank">{}</a>',
            doctor.certificate.url,
            _("View Certificate"),
        )
    certificate_link.short_description = _("Certificate")


class SpecialtyFilter(MultipleDropdownFilter):
    title = _("Main Specialty")
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
class SpecialtyAdmin(SimpleHistoryAdmin, ModelAdmin, ImportExportModelAdmin):
    import_form_class = ImportForm
    export_form_class = SelectableFieldsExportForm

    list_display = ["id", "name_en", "name_ar"]
    list_filter_submit = True
    list_filter = [SpecialtyFilter]
    search_fields = ["name_en", "name_ar"]
    inlines = [SpecialtyInline]


class AchievementDoctorFilter(admin.SimpleListFilter):
    title = pgettext_lazy("the_doctor", "Doctor")
    parameter_name = "doctor_id"

    def lookups(self, request, model_admin):
        doctors = Doctor.objects.with_user().all()
        return [(doctor.user.id, str(doctor.user)) for doctor in doctors]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(doctor_id=self.value())
        return queryset


@admin.register(Achievement)
class AchievementAdmin(SimpleHistoryAdmin, ModelAdmin, ImportExportModelAdmin):
    import_form_class = ImportForm
    export_form_class = SelectableFieldsExportForm

    list_display = ["id", "title", "description", "doctor", "created_at", "updated_at"]
    list_filter = [AchievementDoctorFilter, "created_at", "updated_at"]
    search_fields = ["title", "description"]
    readonly_fields = ["created_at", "updated_at"]
