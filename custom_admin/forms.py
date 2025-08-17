from django.utils.translation import gettext_lazy as _
from django.forms import ValidationError
from django.conf import settings

from django import forms

from rest_framework.exceptions import AuthenticationFailed
from unfold.layout import Submit
from unfold.widgets import UnfoldAdminTextInputWidget, UnfoldAdminPasswordInput

from crispy_forms.layout import Layout, Field
from crispy_forms.helper import FormHelper

from users.services import OTPService
from users.models import CustomUser as User

otp_service = OTPService()

PASSWORD_RESET_KEY = "forgot-password:user:%(user)s"


class PasswordResetFormHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.form_id = "password-reset-form"
        self.form_add = True
        # Ensure spacing between field(s) and submit row by adding class to the form tag
        self.attrs = {"class": "space-y-4"}
        # Ensure the submit row (inputs container) gets top margin
        self.field_class = "mt-4"
        self.form_method = "post"
        self.form_tag = True
        self.layout = Layout(
            Field("phone", wrapper_class="mb-4"),
        )
        self.add_input(Submit("submit", _("Submit"), css_class="mt-2"))


class PasswordResetForm(forms.Form):
    phone = forms.CharField(
        label=_("Phone number"),
        max_length=10,
        widget=UnfoldAdminTextInputWidget(
            attrs={"placeholder": _("Enter your phone number")}
        ),
        required=True,
    )

    def clean_phone(self):
        phone = self.cleaned_data["phone"]
        if settings.DEBUG and not settings.TESTING:
            if phone not in settings.SAFE_PHONE_NUMBERS:
                raise ValidationError(
                    _("This phone number is not allowed during development.")
                )
        if not phone.startswith("09"):
            raise ValidationError(_("Phone number must start with '09'."))

        return phone


class PasswordResetConfirmFormHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.form_id = "password-reset-confirm-form"
        self.form_add = True
        # Ensure spacing between field(s) and submit row by adding class to the form tag
        self.attrs = {"class": "space-y-4"}
        # Ensure the submit row (inputs container) gets top margin
        self.field_class = "mt-4"
        self.form_method = "post"
        self.form_tag = True
        self.layout = Layout(
            Field("phone"),
            Field("otp", wrapper_class="mb-4"),
        )
        self.add_input(Submit("resend", _("Resend code"), css_class="mt-2"))
        self.add_input(Submit("submit", _("Submit"), css_class="mt-2"))


class PasswordResetConfirmForm(forms.Form):
    phone = forms.CharField(widget=forms.HiddenInput())
    otp = forms.CharField(
        label=_("Code"),
        min_length=5,
        max_length=5,
        widget=UnfoldAdminTextInputWidget(attrs={"placeholder": _("Enter your code")}),
        required=False,
    )

    def clean_otp(self):
        otp = self.cleaned_data["otp"]
        if not otp:
            raise ValidationError(_("This field is required."))
        if not otp.isdigit():
            raise ValidationError(_("Code must be a number."))
        return otp

    def clean(self):
        cleaned_data = super().clean()
        # If field-level validation failed (e.g., non-digit otp), stop here
        if self.errors:
            return cleaned_data

        phone = cleaned_data.get("phone")
        otp = cleaned_data.get("otp")
        try:
            user = User.objects.get(phone=phone, role=User.Role.ADMIN)
        except User.DoesNotExist:
            self.add_error("otp", _("Invalid code."))
            return cleaned_data

        key = PASSWORD_RESET_KEY % {"user": user.id}
        try:
            otp_service.validate(key, otp)
        except AuthenticationFailed:
            self.add_error("otp", _("Invalid code."))

        return cleaned_data


class PasswordResetCompleteFormHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.form_id = "password-reset-complete-form"
        self.form_add = True
        # Ensure spacing between field(s) and submit row by adding class to the form tag
        self.attrs = {"class": "space-y-4"}
        # Ensure the submit row (inputs container) gets top margin
        self.field_class = "mt-4"
        self.form_method = "post"
        self.form_tag = True
        self.layout = Layout(
            Field("password", wrapper_class="mb-4"),
            Field("password_confirm", wrapper_class="mb-4"),
        )
        self.add_input(Submit("submit", _("Submit"), css_class="mt-2"))


class PasswordResetCompleteForm(forms.Form):
    password = forms.CharField(
        label=_("Password"),
        min_length=8,
        widget=UnfoldAdminPasswordInput(attrs={"placeholder": _("Enter your password")}),
        required=True,
    )
    password_confirm = forms.CharField(
        label=_("Confirm password"),
        min_length=8,
        widget=UnfoldAdminPasswordInput(attrs={"placeholder": _("Confirm your password")}),
        required=True,
    )

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")
        if password != password_confirm:
            self.add_error("password_confirm", _("Passwords do not match."))
        return cleaned_data