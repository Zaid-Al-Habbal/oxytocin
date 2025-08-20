from django.contrib import admin
from django.contrib.admin.exceptions import NotRegistered
from django.contrib.auth.models import User, Group

from unfold.forms import AdminPasswordChangeForm
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
from .forms import CustomUserCreationForm, CustomUserChangeForm


def safe_unregister(model):
    try:
        admin.site.unregister(model)
    except NotRegistered:
        pass


for model in [User, Group, BlacklistedToken, OutstandingToken]:
    safe_unregister(model)


@admin.register(User)
class UserAdmin(SimpleHistoryAdmin, ModelAdmin, ImportExportModelAdmin):
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    change_password_form = AdminPasswordChangeForm
    import_form_class = ImportForm
    export_form_class = SelectableFieldsExportForm

    list_display = [
        "id",
        "first_name",
        "last_name",
        "phone",
        "email",
        "role",
        "is_active",
        "is_staff",
        "is_superuser",
    ]
    list_filter = ["role", "is_active", "is_staff", "is_superuser"]
    search_fields = ["first_name", "last_name", "phone", "email"]
    readonly_fields = ["created_at", "updated_at"]

    def get_form(self, request, obj=None, **kwargs):
        """Use creation form on add view and change form on change view."""
        defaults = {}
        if obj is None:
            defaults["form"] = self.add_form
        else:
            defaults["form"] = self.form
        defaults.update(kwargs)
        return super().get_form(request, obj, **defaults)
