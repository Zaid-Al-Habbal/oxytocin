from celery import shared_task

from .models import CustomUser as User
from .services import SMSService


sms_service = SMSService()


@shared_task
def send_sms(user_id, message):
    try:
        user = User.objects.get(id=user_id)
        return sms_service.send_sms(user.phone, message)
    except User.DoesNotExist:
        return {
            "error": "User.DoesNotExist",
            "user_id": user_id,
        }


@shared_task
def send_bulk_sms(user_ids, message):
    recipients = []
    not_found_ids = []
    for user_id in user_ids:
        try:
            user = User.objects.get(id=user_id)
            recipients.append(user.phone)
        except User.DoesNotExist:
            not_found_ids.append(user_id)
    return {
        "result": sms_service.send_bulk_sms(recipients, message),
        "not_found_ids": not_found_ids,
        "errors": len(not_found_ids),
    }
