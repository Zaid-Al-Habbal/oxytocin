from django.contrib import admin
from unfold.admin import ModelAdmin
from import_export.admin import ImportExportModelAdmin
from unfold.contrib.import_export.forms import ExportForm, ImportForm, SelectableFieldsExportForm
from simple_history.admin import SimpleHistoryAdmin

from favorites.models import Favorite


@admin.register(Favorite)
class FavoriteAdmin(SimpleHistoryAdmin, ModelAdmin, ImportExportModelAdmin):
    import_form_class = ImportForm
    export_form_class = SelectableFieldsExportForm
    
    list_display = ["id", "patient", "doctor", "created_at"]
    list_filter = ["patient", "doctor"]
    readonly_fields = ["created_at"]
