from django.utils.translation import pgettext_lazy

from django.contrib import admin
from unfold.admin import ModelAdmin
from unfold.contrib.filters.admin import SliderNumericFilter, RangeDateFilter
from import_export.admin import ImportExportModelAdmin
from unfold.contrib.import_export.forms import ExportForm, ImportForm, SelectableFieldsExportForm
from simple_history.admin import SimpleHistoryAdmin

from patients.models import Patient

from .models import Evaluation


class RateFilter(SliderNumericFilter):
    MAX_DECIMALS = 5
    STEP = 1

class EvaluationPatientFilter(admin.SimpleListFilter):
    title = pgettext_lazy("the_patient", "Patient")
    parameter_name = "patient_id"
    
    def lookups(self, request, model_admin):
        return [(patient.id, str(patient)) for patient in Patient.objects.all()]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(patient_id=self.value())
        return queryset

@admin.register(Evaluation)
class EvaluationAdmin(SimpleHistoryAdmin, ModelAdmin, ImportExportModelAdmin):
    import_form_class = ImportForm
    export_form_class = SelectableFieldsExportForm
    
    list_display = ["id", "patient", "appointment", "rate", "created_at", "updated_at"]
    list_filter_submit = True
    list_filter = [
        EvaluationPatientFilter,
        ("rate", RateFilter),
        ("created_at", RangeDateFilter),
        ("updated_at", RangeDateFilter),
    ]
    search_fields = ["patient__user__first_name", "patient__user__last_name", "patient__user__phone"]
    readonly_fields = ["created_at", "updated_at"]
