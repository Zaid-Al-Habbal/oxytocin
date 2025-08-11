from django.contrib import admin

from unfold.admin import ModelAdmin
from import_export.admin import ImportExportModelAdmin
from unfold.contrib.import_export.forms import ExportForm, ImportForm, SelectableFieldsExportForm
from simple_history.admin import SimpleHistoryAdmin
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken

from .models import CustomUser as User

admin.site.unregister(BlacklistedToken)
admin.site.unregister(OutstandingToken)

@admin.register(User)
class UserAdmin(SimpleHistoryAdmin, ModelAdmin, ImportExportModelAdmin):
    import_form_class = ImportForm
    export_form_class = SelectableFieldsExportForm

    list_display = [
        "id",
        "first_name",
        "last_name",
        "email",
        "role",
        "is_active",
        "is_staff",
        "is_superuser",
    ]
    list_filter = ["role", "is_active", "is_staff", "is_superuser"]
    search_fields = ["first_name", "last_name", "email"]
    readonly_fields = ["created_at", "updated_at"]
