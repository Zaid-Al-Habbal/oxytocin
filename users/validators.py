from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
import re


class UpperLowerCaseValidator:
    def validate(self, password, user=None):
        if not any(c.islower() for c in password):
            raise ValidationError(
                _("Password must contain at least one lowercase letter."),
                code="password_no_lower",
            )
        if not any(c.isupper() for c in password):
            raise ValidationError(
                _("Password must contain at least one uppercase letter."),
                code="password_no_upper",
            )

    def get_help_text(self):
        return _("Your password must contain both uppercase and lowercase letters.")


class DigitSymbolValidator:
    def validate(self, password, user=None):
        if not any(c.isdigit() for c in password):
            raise ValidationError(
                _("Password must contain at least one number."),
                code="password_no_number",
            )
        if not re.search(r"[!@#$%^&*()_\-+=]", password):
            raise ValidationError(
                _(
                    "Password must contain at least one special character (!@#$%^&*()_-+=)."
                ),
                code="password_no_special",
            )

    def get_help_text(self):
        return _(
            "Your password must contain at least one number and one special character (!@#$%^&*()_-+=)."
        )
