from django.contrib import admin

from unfold.admin import ModelAdmin
from import_export.admin import ImportExportModelAdmin
from unfold.contrib.import_export.forms import ExportForm, ImportForm, SelectableFieldsExportForm
from simple_history.admin import SimpleHistoryAdmin

from .models import Archive, ArchiveAccessPermission


@admin.register(Archive)
class ArchiveAdmin(SimpleHistoryAdmin, ModelAdmin, ImportExportModelAdmin):
    import_form_class = ImportForm
    export_form_class = SelectableFieldsExportForm
    
    list_display = [
        "id",
        "main_complaint",
        "patient",
        "doctor",
        "appointment",
        "specialty",
        "created_at",
    ]
    list_filter = [
        ("patient__user", admin.RelatedOnlyFieldListFilter),
        ("doctor__user", admin.RelatedOnlyFieldListFilter),
        ("appointment", admin.RelatedOnlyFieldListFilter),
        ("specialty", admin.RelatedOnlyFieldListFilter),
    ]
    search_fields = [
        "main_complaint",
        "patient__user__first_name",
        "patient__user__last_name",
        "doctor__user__first_name",
        "doctor__user__last_name",
        "specialty__name_en",
        "specialty__name_ar",
    ]
    autocomplete_fields = ["specialty"]
    readonly_fields = ["created_at"]


@admin.register(ArchiveAccessPermission)
class ArchiveAccessPermissionAdmin(SimpleHistoryAdmin, ModelAdmin, ImportExportModelAdmin):
    import_form_class = ImportForm
    export_form_class = SelectableFieldsExportForm
    
    list_display = ["id", "patient", "doctor", "specialty"]
    list_filter = [
        ("patient__user", admin.RelatedOnlyFieldListFilter),
        ("doctor__user", admin.RelatedOnlyFieldListFilter),
        ("specialty", admin.RelatedOnlyFieldListFilter),
    ]
    search_fields = [
        "patient__user__first_name",
        "patient__user__last_name",
        "doctor__user__first_name",
        "doctor__user__last_name",
        "specialty__name_en",
        "specialty__name_ar",
    ]
    readonly_fields = ["created_at"]
