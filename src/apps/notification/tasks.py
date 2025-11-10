import time

from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone

from apps.account.models import User


@shared_task(bind=True, max_retries=5, default_retry_delay=3)
def send_welcome_email_task(self, user_id: int):
    try:
        for attempt in range(5):
            try:
                user = User.objects.get(id=user_id)
                break
            except User.DoesNotExist:
                if attempt == 4:
                    raise
                time.sleep(0.5)

        subject = "Bem-vindo à nossa plataforma!"
        from_email = settings.DEFAULT_FROM_EMAIL
        to = [user.email]

        context = {"user": user, "current_year": timezone.now().year}

        html_content = render_to_string(
            "notification/email/welcome.html", context)
        text_content = f"Olá {user.username}, bem-vindo à nossa plataforma!"

        msg = EmailMultiAlternatives(subject, text_content, from_email, to)
        msg.attach_alternative(html_content, "text/html")
        msg.send()

    except User.DoesNotExist as exc:
        raise self.retry(exc=exc, countdown=3)

    except Exception as exc:
        raise self.retry(exc=exc, countdown=5)
