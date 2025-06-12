from django.contrib import admin
from .models import Appointment, Attachment


class AttachmentInline(admin.TabularInline):
    model = Attachment
    extra = 1  # Number of empty attachment forms shown by default
    fields = ('document', 'created_at')
    readonly_fields = ('created_at',)


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = (
        'id', 
        'patient', 
        'clinic', 
        'visit_date', 
        'visit_time', 
        'status', 
        'actual_start_time', 
        'actual_end_time',
        'cancelled_at', 
        'cancelled_by'
    )
    list_filter = ('visit_date', 'status', 'clinic')
    search_fields = ('patient__first_name', 'patient__last_name', 'clinic__id')
    ordering = ('-visit_date', '-visit_time')
    autocomplete_fields = ['patient', 'clinic', 'cancelled_by']


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'appointment', 'document', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('appointment__id',)
    autocomplete_fields = ['appointment']
