from celery import shared_task

from .services import SMSService


sms_service = SMSService()


@shared_task
def send_sms(phone, message):
    recipient = f"+963{phone[1:]}"
    return sms_service.send_sms(recipient, message)


@shared_task
def send_bulk_sms(phones, message):
    recipients = [f"+963{phone[1:]}" for phone in phones]
    return sms_service.send_bulk_sms(recipients, message)
