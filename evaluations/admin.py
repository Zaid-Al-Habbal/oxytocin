from django.contrib import admin

from .models import Evaluation


@admin.register(Evaluation)
class EvaluationAdmin(admin.ModelAdmin):
    list_display = ["id", "patient", "appointment", "rate", "created_at", "updated_at"]
    list_filter = [
        ("patient", admin.RelatedOnlyFieldListFilter),
        ("appointment", admin.RelatedOnlyFieldListFilter),
        "rate",
        "created_at",
        "updated_at",
    ]
    list_editable = ["rate"]
    readonly_fields = ["created_at", "updated_at"]
