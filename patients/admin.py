from django.contrib import admin
from django.contrib.gis.db import models

from unfold.admin import ModelAdmin
from import_export.admin import ImportExportModelAdmin
from unfold.contrib.import_export.forms import ExportForm, ImportForm, SelectableFieldsExportForm
from simple_history.admin import SimpleHistoryAdmin
import mapwidgets

from .models import Patient, PatientSpecialtyAccess


@admin.register(Patient)
class PatientAdmin(SimpleHistoryAdmin, ModelAdmin, ImportExportModelAdmin):
    import_form_class = ImportForm
    export_form_class = SelectableFieldsExportForm
    
    list_display = ["user_id", "job", "address", "blood_type"]
    list_filter = ["blood_type"]
    search_fields = ["job"]
    formfield_overrides = {
        models.PointField: {"widget": mapwidgets.GoogleMapPointFieldWidget}
    }


@admin.register(PatientSpecialtyAccess)
class PatientSpecialtyAccessAdmin(SimpleHistoryAdmin, ModelAdmin, ImportExportModelAdmin):
    import_form_class = ImportForm
    export_form_class = SelectableFieldsExportForm
    
    list_display = ["id", "patient", "specialty", "visibility"]
    list_filter = [
        ("patient__user", admin.RelatedOnlyFieldListFilter),
        ("specialty", admin.RelatedOnlyFieldListFilter),
        "visibility",
    ]
    list_editable = ["visibility"]
    search_fields = [
        "patient__user__first_name",
        "patient__user__last_name",
        "specialty__name_en",
        "specialty__name_ar",
        "visibility",
    ]
    readonly_fields = ["created_at"]
