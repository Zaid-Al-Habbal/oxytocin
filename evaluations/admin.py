from django.contrib import admin
from unfold.admin import ModelAdmin
from unfold.contrib.filters.admin import SliderNumericFilter

from .models import Evaluation


class RateFilter(SliderNumericFilter):
    MAX_DECIMALS = 5
    STEP = 1


@admin.register(Evaluation)
class EvaluationAdmin(ModelAdmin):
    list_display = ["id", "patient", "appointment", "rate", "created_at", "updated_at"]
    list_filter = [
        ("patient", admin.RelatedOnlyFieldListFilter),
        ("rate", RateFilter),
        "created_at",
        "updated_at",
    ]
    list_editable = ["rate"]
    readonly_fields = ["created_at", "updated_at"]
