from django.contrib import admin
from unfold.admin import ModelAdmin
from unfold.contrib.filters.admin import SliderNumericFilter
from import_export.admin import ImportExportModelAdmin
from unfold.contrib.import_export.forms import ExportForm, ImportForm, SelectableFieldsExportForm
from simple_history.admin import SimpleHistoryAdmin

from .models import Evaluation


class RateFilter(SliderNumericFilter):
    MAX_DECIMALS = 5
    STEP = 1


@admin.register(Evaluation)
class EvaluationAdmin(SimpleHistoryAdmin, ModelAdmin, ImportExportModelAdmin):
    import_form_class = ImportForm
    export_form_class = SelectableFieldsExportForm
    
    list_display = ["id", "patient", "appointment", "rate", "created_at", "updated_at"]
    list_filter = [
        ("patient", admin.RelatedOnlyFieldListFilter),
        ("rate", RateFilter),
        "created_at",
        "updated_at",
    ]
    list_editable = ["rate"]
    readonly_fields = ["created_at", "updated_at"]
