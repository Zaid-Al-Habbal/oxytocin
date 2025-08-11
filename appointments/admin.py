from django.contrib import admin

from unfold.admin import ModelAdmin, TabularInline
from import_export.admin import ImportExportModelAdmin
from unfold.contrib.import_export.forms import ExportForm, ImportForm, SelectableFieldsExportForm
from simple_history.admin import SimpleHistoryAdmin

from .models import Appointment, Attachment


class AttachmentInline(TabularInline):
    model = Attachment
    extra = 1  # Number of empty attachment forms shown by default
    fields = ("document", "created_at")
    readonly_fields = ("created_at",)


@admin.register(Appointment)
class AppointmentAdmin(SimpleHistoryAdmin, ModelAdmin, ImportExportModelAdmin):
    import_form_class = ImportForm
    export_form_class = SelectableFieldsExportForm
    
    list_display = (
        "id",
        "patient",
        "clinic",
        "visit_date",
        "visit_time",
        "status",
        "actual_start_time",
        "actual_end_time",
        "cancelled_at",
        "cancelled_by",
    )
    list_filter = ("visit_date", "status", "clinic")
    ordering = ("-visit_date", "-visit_time")


@admin.register(Attachment)
class AttachmentAdmin(SimpleHistoryAdmin, ModelAdmin, ImportExportModelAdmin):
    import_form_class = ImportForm
    export_form_class = SelectableFieldsExportForm
    
    list_display = ("id", "appointment", "document", "created_at")
    list_filter = ("created_at",)
