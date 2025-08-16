from django.contrib import admin
from django.contrib.gis.db import models

from unfold.admin import ModelAdmin, TabularInline
from simple_history.admin import SimpleHistoryAdmin
from import_export.admin import ImportExportModelAdmin
from unfold.contrib.import_export.forms import ExportForm, ImportForm, SelectableFieldsExportForm

import mapwidgets

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


@admin.register(BannedPatient)
class BannedPatientAdmin(SimpleHistoryAdmin, ModelAdmin, ImportExportModelAdmin):
    import_form_class = ImportForm
    export_form_class = SelectableFieldsExportForm
    
    list_display = ["id", "clinic", "patient", "created_at"]
    readonly_fields = ["created_at"]
    search_fields = ["clinic__phone", "patient__first_name", "patient__last_name"]
