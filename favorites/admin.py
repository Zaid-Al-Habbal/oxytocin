from django.contrib import admin
from unfold.admin import ModelAdmin

from favorites.models import Favorite


@admin.register(Favorite)
class FavoriteAdmin(ModelAdmin):
    list_display = ["id", "patient", "doctor", "created_at"]
    list_filter = ["patient", "doctor"]
    readonly_fields = ["created_at"]
