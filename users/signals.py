from django.utils.translation import gettext_lazy as _
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

from .models import CustomUser as User
from .services import OTPService
from .tasks import send_sms


otp_service = OTPService()


@receiver(post_save, sender=User)
def post_save_user(sender, instance, created, **kwargs):
    if created and not instance.is_superuser and not settings.TESTING:
        otp = otp_service.generate(instance.id)
        message = _("🩺 Welcome to Oxytocin!\nYour signup code is %(otp)s.\nDon't share it with anyone.") % {"otp": otp}
        send_sms.delay(instance.phone, message)
