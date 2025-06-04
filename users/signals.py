from django.utils.translation import gettext_lazy as _
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

from .models import CustomUser as User
from .tasks import send_sms


@receiver(post_save, sender=User)
def post_save_user(sender, instance, created, **kwargs):
    if created and not instance.is_superuser and not settings.TESTING:
        message = _(settings.VERIFICATION_CODE_MESSAGE)
        send_sms.delay(instance.id, message)
