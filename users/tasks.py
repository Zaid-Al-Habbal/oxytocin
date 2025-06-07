from celery import shared_task

from .services import SMSService


sms_service = SMSService()


@shared_task
def send_sms(phone, message):
    return sms_service.send_sms(phone, message)


@shared_task
def send_bulk_sms(phones, message):
    return sms_service.send_bulk_sms(phones, message)
