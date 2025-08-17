from django.utils.translation import gettext_lazy as _
from django.urls import reverse_lazy
from django.contrib.auth import login
from django.views.generic import FormView
from django.contrib import admin

from custom_admin.admin import (
    PatientsLineComponent,
    DoctorsLineComponent,
    AssistantsLineComponent,
)
from custom_admin.forms import (
    PasswordResetForm,
    PasswordResetFormHelper,
    PasswordResetConfirmForm,
    PasswordResetConfirmFormHelper,
    PasswordResetCompleteForm,
    PasswordResetCompleteFormHelper,
    PASSWORD_RESET_KEY,
)

from users.tasks import send_sms
from users.services import OTPService
from users.models import CustomUser as User


otp_service = OTPService()


class PasswordResetView(FormView):
    title = _("Password Reset")
    success_url = reverse_lazy("admin_password_reset_confirm")
    template_name = "registration/password_reset_form.html"

    form_class = PasswordResetForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(admin.site.each_context(self.request))
        context.update({"title": self.title, "form_helper": PasswordResetFormHelper()})

        return context

    def form_valid(self, form):
        phone = form.cleaned_data["phone"]
        try:
            user: User = User.objects.not_deleted().get(
                phone=phone,
                role=User.Role.ADMIN,
            )
        except User.DoesNotExist:
            # Keep phone available for the next step even if the user lookup fails
            self.request.session["password_reset_phone"] = phone
            return super().form_valid(form)

        key = PASSWORD_RESET_KEY % {"user": user.id}
        otp = otp_service.generate(key)
        message = _(
            "🩺 Oxytocin:\nUse code %(otp)s to reset your password.\nDon’t share this code with anyone."
        ) % {"otp": otp}
        send_sms.delay(user.phone, message)

        # Keep phone available for the next step
        self.request.session["password_reset_phone"] = phone

        return super().form_valid(form)


class PasswordResetConfirmView(FormView):
    title = _("Password Reset Confirmation")
    success_url = reverse_lazy("admin_password_reset_complete")
    template_name = "registration/password_reset_confirm.html"

    form_class = PasswordResetConfirmForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(admin.site.each_context(self.request))
        context.update(
            {"title": self.title, "form_helper": PasswordResetConfirmFormHelper()}
        )

        return context

    def form_valid(self, form):
        phone = form.cleaned_data["phone"]
        user = User.objects.not_deleted().get(phone=phone, role=User.Role.ADMIN)
        login(self.request, user)
        return super().form_valid(form)

    def get_initial(self):
        initial = super().get_initial()
        phone = self.request.session.get(
            "password_reset_phone"
        ) or self.request.GET.get("phone")
        if phone:
            initial["phone"] = phone
        return initial


class PasswordResetCompleteView(FormView):
    title = _("Password Reset Complete")
    success_url = reverse_lazy("admin:index")
    template_name = "registration/password_reset_complete.html"

    form_class = PasswordResetCompleteForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(admin.site.each_context(self.request))
        context.update(
            {"title": self.title, "form_helper": PasswordResetCompleteFormHelper()}
        )
        return context

    def form_valid(self, form):
        user: User = self.request.user
        user.set_password(form.cleaned_data["password"])
        user.save()
        login(self.request, user)
        return super().form_valid(form)


def dashboard_callback(request, context):
    context.update(
        {
            "patients_count": PatientsLineComponent(request).get_count(),
            "doctors_count": DoctorsLineComponent(request).get_count(),
            "assistants_count": AssistantsLineComponent(request).get_count(),
        }
    )

    return context
