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
from django.contrib import messages


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

    def post(self, request, *args, **kwargs):
        # Allow resending code without validating the OTP field
        if request.POST.get("resend") is not None:
            phone = request.POST.get("phone") or request.session.get(
                "password_reset_phone"
            )
            if phone:
                try:
                    user = User.objects.not_deleted().get(
                        phone=phone, role=User.Role.ADMIN
                    )
                    key = PASSWORD_RESET_KEY % {"user": user.id}
                    otp = otp_service.generate(key)
                    message = _(
                        "🩺 Oxytocin:\nUse code %(otp)s to reset your password.\nDon’t share this code with anyone."
                    ) % {"otp": otp}
                    send_sms.delay(user.phone, message)

                except User.DoesNotExist:
                    pass

                messages.success(request, _("A new code has been sent."))
                # Persist phone for subsequent requests
                request.session["password_reset_phone"] = phone

            # Re-render with an unbound form (pre-filled from initial) to avoid errors
            form = self.form_class(initial=self.get_initial())
            return self.render_to_response(self.get_context_data(form=form))

        return super().post(request, *args, **kwargs)


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
