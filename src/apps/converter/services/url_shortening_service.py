from enum import Enum

from django.db import transaction
from django.utils.translation import gettext_lazy as _

from apps.billing.services.wallet_service import WalletService
from apps.converter.models import Url


class ShortenResult(Enum):
    CREATED = "created"
    EXISTS = "exists"


class UrlShorteningService:

    @staticmethod
    @transaction.atomic
    def shorten(*, user, client_ip, url_object, is_direct, create_new=False):

        cost = 2 if is_direct else 1

        existing = UrlShorteningService._find_existing(
            user, client_ip, url_object)

        if existing and not create_new:
            return url_object, ShortenResult.EXISTS

        if user.is_authenticated:
            WalletService.debit(
                wallet=user.wallet,
                amount=cost,
                source=_("URL shortening")
            )

        url_object.created_by = user if user.is_authenticated else None
        url_object.created_by_ip = client_ip
        url_object.is_direct = is_direct
        url_object.save()

        return url_object, ShortenResult.CREATED

    @staticmethod
    def _find_existing(user, client_ip, url_object):
        if user.is_authenticated:
            return Url.objects.filter(
                original_url=url_object.original_url,
                created_by=user
            ).first()
        return Url.objects.filter(
            original_url=url_object.original_url,
            created_by=None,
            created_by_ip=client_ip
        ).first()
