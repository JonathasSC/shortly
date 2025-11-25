from django.dispatch import receiver
from axes.signals import axes_lockout
from apps.security.services import ExponentialBanService
import logging

logger = logging.getLogger("security")

@receiver(axes_lockout)
def on_lockout(sender, request, username, ip_address, **kwargs):
    delay = ExponentialBanService.register_lockout(username)

    logger.warning({
        "event": "security_lockout",
        "username": username,
        "ip": ip_address,
        "delay": delay,
    })
