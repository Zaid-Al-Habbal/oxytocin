from django.contrib import admin
from .models import ClinicSchedule

@admin.register(ClinicSchedule)
class ClinicScheduleAdmin(admin.ModelAdmin):
    list_display = ('clinic', 'day_name', 'special_date', 'is_available')
    list_filter = ('day_name', 'is_available', 'special_date')