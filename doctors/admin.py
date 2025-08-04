from django.contrib import admin

from nested_admin import nested

from .models import Doctor, Specialty, DoctorSpecialty, Achievement


class DoctorSpecialtyInline(nested.NestedTabularInline):
    model = DoctorSpecialty
    autocomplete_fields = ["specialty"]


@admin.register(Doctor)
class DoctorAdmin(nested.NestedModelAdmin):
    list_display = [
        "user_id",
        "user",
        "about",
        "education",
        "start_work_date",
        "status",
        "certificate",
    ]
    list_filter = ["status"]
    list_editable = ["status"]
    inlines = [DoctorSpecialtyInline]


class SpecialtyFilter(admin.SimpleListFilter):
    title = "Main Specialty"
    parameter_name = "main_specialty"

    def lookups(self, request, model_admin):
        main_specialties = Specialty.objects.main_specialties_only()
        return [
            (main_specialty.id, str(main_specialty))
            for main_specialty in main_specialties
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(main_specialties__id=self.value())
        return queryset


@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display = ["id", "name_en", "name_ar"]
    list_filter = [SpecialtyFilter]
    search_fields = ["name_en", "name_ar"]


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ["id", "title", "description", "doctor", "created_at", "updated_at"]
    list_filter = ["doctor", "created_at", "updated_at"]
    search_fields = ["title", "description"]
    readonly_fields = ["created_at", "updated_at"]