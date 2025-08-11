from django.contrib import admin

from unfold.admin import ModelAdmin
from import_export.admin import ImportExportModelAdmin
from unfold.contrib.import_export.forms import ExportForm, ImportForm, SelectableFieldsExportForm
from simple_history.admin import SimpleHistoryAdmin

from assistants.models import Assistant


# Register your models here.
@admin.register(Assistant)
class AssistantAdmin(SimpleHistoryAdmin, ModelAdmin, ImportExportModelAdmin):
    import_form_class = ImportForm
    export_form_class = SelectableFieldsExportForm
    
    list_display = [
        "user_id",
        "user",
        "clinic",
        "joined_clinic_at",
        "years_of_experience",
    ]
    search_fields = [
        "user__first_name",
        "user__last_name",
    ]
