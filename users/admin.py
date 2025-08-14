from django.contrib import admin
from django.contrib.admin.exceptions import NotRegistered
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.models import User, Group

from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm
from unfold.admin import ModelAdmin
from import_export.admin import ImportExportModelAdmin
from unfold.contrib.import_export.forms import (
    ImportForm,
    SelectableFieldsExportForm,
)
from simple_history.admin import SimpleHistoryAdmin
from rest_framework_simplejwt.token_blacklist.models import (
    OutstandingToken,
    BlacklistedToken,
)

from .models import CustomUser as User


def safe_unregister(model):
    try:
        admin.site.unregister(model)
    except NotRegistered:
        pass


for model in [User, Group, BlacklistedToken, OutstandingToken]:
    safe_unregister(model)


@admin.register(User)
class UserAdmin(SimpleHistoryAdmin, ModelAdmin, ImportExportModelAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm
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
