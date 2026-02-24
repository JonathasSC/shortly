from django.db import transaction
from django.utils.translation import gettext_lazy as translate

from apps.billing.services.wallet_service import WalletService
from apps.converter.enums import ShortenResult
from apps.converter.models import Url, UrlMetadata
from apps.converter.services.pricing_service import PricingService


class UrlShorteningService:
    @staticmethod
    @transaction.atomic
    def shorten(
        *,
        user,
        client_ip,
        url_object,
        is_direct: bool,
        is_permanent: bool,
        create_new: bool = False,
    ):
        cost = PricingService.calculate_cost(
            is_direct=is_direct,
            is_permanent=is_permanent,
        )

        existing = UrlShorteningService._find_existing(
            user=user,
            client_ip=client_ip,
            url_object=url_object,
            is_direct=is_direct,
            is_permanent=is_permanent,
        )

        if existing and not create_new:
            return existing, ShortenResult.EXISTS

        if user.is_authenticated:
            WalletService.debit(
                wallet=user.wallet,
                amount=cost,
                source=translate("URL shortening"),
            )

        url_object.created_by = user if user.is_authenticated else None
        url_object.created_by_ip = client_ip
        url_object.save()

        metadata, _ = UrlMetadata.objects.get_or_create(url=url_object)
        metadata.is_direct = is_direct
        metadata.is_permanent = is_permanent
        metadata.save()

        return url_object, ShortenResult.CREATED

    @staticmethod
    def _find_existing(
        *,
        user,
        client_ip,
        url_object,
        is_direct: bool,
        is_permanent: bool,
    ):
        url_filters = {
            "original_url": url_object.original_url,
        }

        if user.is_authenticated:
            url_filters["created_by"] = user
        else:
            url_filters["created_by"] = None
            url_filters["created_by_ip"] = client_ip

        return (
            Url.objects.filter(**url_filters)
            .filter(
                metadata__is_direct=is_direct,
                metadata__is_permanent=is_permanent,
            )
            .select_related("metadata")
            .first()
        )
