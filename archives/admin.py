from django.contrib import admin

from .models import Archive, ArchiveAccessPermission


@admin.register(Archive)
class ArchiveAdmin(admin.ModelAdmin):
    list_display = [
        "main_complaint",
        "patient",
        "doctor",
        "appointment",
        "specialty",
        "created_at",
    ]
    list_filter = [
        ("patient__user", admin.RelatedOnlyFieldListFilter),
        ("doctor__user", admin.RelatedOnlyFieldListFilter),
        ("appointment", admin.RelatedOnlyFieldListFilter),
        ("specialty", admin.RelatedOnlyFieldListFilter),
    ]
    search_fields = [
        "main_complaint",
        "patient__user__first_name",
        "patient__user__last_name",
        "doctor__user__first_name",
        "doctor__user__last_name",
        "specialty__name_en",
        "specialty__name_ar",
    ]
    readonly_fields = ["created_at"]


@admin.register(ArchiveAccessPermission)
class ArchiveAccessPermissionAdmin(admin.ModelAdmin):
    list_display = ["patient", "doctor", "specialty"]
    list_filter = [
        ("patient__user", admin.RelatedOnlyFieldListFilter),
        ("doctor__user", admin.RelatedOnlyFieldListFilter),
        ("specialty", admin.RelatedOnlyFieldListFilter),
    ]
    search_fields = [
        "patient__user__first_name",
        "patient__user__last_name",
        "doctor__user__first_name",
        "doctor__user__last_name",
        "specialty__name_en",
        "specialty__name_ar",
    ]
    readonly_fields = ["created_at"]
