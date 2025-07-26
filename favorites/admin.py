from django.contrib import admin

from favorites.models import Favorite


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ["patient", "doctor", "created_at"]
    list_filter = ["patient", "doctor"]
    readonly_fields = ["created_at"]
