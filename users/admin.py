from django.contrib import admin
from .models import CustomUser as User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ["id", "first_name", "last_name", "email", "role", "is_active", "is_staff", "is_superuser"]
    list_filter = ["role", "is_active", "is_staff", "is_superuser"]
    search_fields = ["first_name", "last_name", "email"]
    readonly_fields = ["created_at", "updated_at"]