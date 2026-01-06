import time

from celery import shared_task
from apps.notification.models import EmailOutbox
from apps.notification.mailers import send_welcome_email


@shared_task(bind=True, autoretry_for=(Exception,), retry_kwargs={"max_retries": 5, "countdown": 10})
def process_email_outbox_task(self):
    for outbox in EmailOutbox.objects.select_for_update(skip_locked=True).filter(status="pending")[:20]:
        try:
            if outbox.template == "welcome":
                send_welcome_email(outbox.user)

            outbox.status = EmailOutbox.Status.SENT
            outbox.save(update_fields=["status"])

        except Exception as exc:
            outbox.attempts += 1
            outbox.last_error = str(exc)

            if outbox.attempts >= 5:
                outbox.status = EmailOutbox.Status.FAILED

            outbox.save(update_fields=["attempts", "status", "last_error"])
