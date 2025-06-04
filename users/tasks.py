from celery import shared_task

from .models import CustomUser as User
from .services import SMSService, OTPService


sms_service = SMSService()
otp_service = OTPService()


@shared_task
def send_sms(user_id, message):
    try:
        user = User.objects.get(id=user_id)
        otp = otp_service.generate(user_id)
        result = sms_service.send_sms(user.phone, message % {"otp": otp})
        return result
    except User.DoesNotExist:
        return None
