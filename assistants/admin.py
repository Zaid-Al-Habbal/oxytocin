from django.contrib import admin

from unfold.admin import ModelAdmin

from assistants.models import Assistant


# Register your models here.
@admin.register(Assistant)
class AssistantAdmin(ModelAdmin):
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
