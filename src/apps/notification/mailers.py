from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone


def send_welcome_email(user):
    subject = "Bem-vindo à nossa plataforma!"
    context = {"user": user, "current_year": timezone.now().year}

    html = render_to_string("notification/email/welcome.html", context)
    text = f"Olá {user.username}, bem-vindo à nossa plataforma!"

    msg = EmailMultiAlternatives(
        subject, text, settings.DEFAULT_FROM_EMAIL, [user.email])
    msg.attach_alternative(html, "text/html")
    msg.send()
