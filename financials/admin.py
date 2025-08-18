from django.contrib import admin

from unfold.admin import ModelAdmin

from .models import Financial, Payment


@admin.register(Financial)
class FinancialAdmin(ModelAdmin):
    list_display = ["id", "clinic", "patient", "cost", "created_at"]
    readonly_fields = ["created_at", "updated_at"]
    search_fields = ["clinic__phone", "patient__first_name", "patient__last_name"]


@admin.register(Payment)
class PaymentAdmin(ModelAdmin):
    list_display = ["id", "clinic", "patient", "cost", "created_at"]
    list_filter = ["clinic", "patient"]
    readonly_fields = ["created_at"]
    search_fields = ["clinic__phone", "patient__first_name", "patient__last_name"]
