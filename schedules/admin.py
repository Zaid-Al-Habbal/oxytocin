from django.contrib import admin
from .models import ClinicSchedule, AvailableHour

@admin.register(ClinicSchedule)
class ClinicScheduleAdmin(admin.ModelAdmin):
    list_display = ('clinic', 'day_name', 'special_date', 'is_available')
    list_filter = ('day_name', 'is_available', 'special_date')
    

@admin.register(AvailableHour)
class AvailableHourAdmin(admin.ModelAdmin):
    def clinic(self, obj):
        return obj.schedule.clinic      
    clinic.short_description = 'Clinic'
    list_display = ('id', 'clinic', 'schedule', 'start_hour', 'end_hour', )
    list_filter = ('schedule__clinic', 'schedule__day_name')
    search_fields = ('schedule__clinic__id', 'schedule__clinic__location', 'schedule__day_name')
    ordering = ('schedule', 'start_hour')

    fieldsets = (
        (None, {
            'fields': ('schedule', 'start_hour', 'end_hour')
        }),
        ('Timestamps', {
            'fields': (),
            'classes': ('collapse',),
        }),
    )