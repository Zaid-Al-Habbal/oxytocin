from django.utils.translation import pgettext_lazy
from django.contrib import admin
from django.contrib.gis.db import models

from unfold.admin import ModelAdmin, TabularInline
from simple_history.admin import SimpleHistoryAdmin
from import_export.admin import ImportExportModelAdmin
from unfold.contrib.import_export.forms import ExportForm, ImportForm, SelectableFieldsExportForm

import mapwidgets

from patients.models import Patient

from .models import BannedPatient, Clinic, ClinicImage


class ClinicImageInline(TabularInline):
    model = ClinicImage
    raw_id_fields = ["clinic"]


@admin.register(Clinic)
class ClinicAdmin(SimpleHistoryAdmin, ModelAdmin, ImportExportModelAdmin):
    import_form_class = ImportForm
    export_form_class = SelectableFieldsExportForm
    
    list_display = ["id", "doctor", "address", "phone"]
    search_fields = ["phone"]
    inlines = [ClinicImageInline]
    formfield_overrides = {
        models.PointField: {"widget": mapwidgets.GoogleMapPointFieldWidget}
    }


class BannedPatientClinicFilter(admin.SimpleListFilter):
    title = pgettext_lazy("the_clinic", "Clinic")
    parameter_name = "clinic_id"
    
    def lookups(self, request, model_admin):
        return [(clinic.id, str(clinic)) for clinic in Clinic.objects.all()]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(clinic_id=self.value())
        return queryset

class BannedPatientPatientFilter(admin.SimpleListFilter):
    title = pgettext_lazy("the_patient", "Patient")
    parameter_name = "patient_id"
    
    def lookups(self, request, model_admin):
        return [(patient.id, str(patient)) for patient in Patient.objects.all()]
        
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(patient_id=self.value())
        return queryset
    

@admin.register(BannedPatient)
class BannedPatientAdmin(SimpleHistoryAdmin, ModelAdmin, ImportExportModelAdmin):
    import_form_class = ImportForm
    export_form_class = SelectableFieldsExportForm
    
    list_display = ["id", "clinic", "patient", "created_at"]
    list_filter = [BannedPatientClinicFilter, BannedPatientPatientFilter]
    readonly_fields = ["created_at"]
    search_fields = ["clinic__phone", "patient__first_name", "patient__last_name"]
