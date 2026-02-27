from django.conf import settings
from django.db import transaction
from django.db.models import F
from django.utils.translation import gettext_lazy as translate
from hashids import Hashids

from apps.billing.services.wallet_service import WalletService
from apps.converter.enums import ShortenResult
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
        from apps.converter.models import UrlMetadata
        
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

        if not url_object.short_code:
            url_object.short_code = ShortCodeService.encode(url_object.id)
            url_object.save(update_fields=["short_code"])
                
        url_object.save()
        
        metadata, _ = UrlMetadata.objects.get_or_create(url=url_object)
        metadata.is_direct = is_direct
        metadata.is_permanent = is_permanent
        metadata.save()

        UrlMetadata.objects.update_or_create(
            url=url_object,
            defaults={
                "is_direct": is_direct,
                "is_permanent": is_permanent
            }
        )
        
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
        from apps.converter.models import Url
        
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


class ShortCodeService:
    _hashids = Hashids(
        salt=settings.SHORT_CODE_SALT,
        min_length=getattr(settings, "SHORT_CODE_MIN_LENGTH", 6),
        alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"
    )

    @staticmethod
    def encode(number: int) -> str:
        if number is None:
            raise ValueError("Cannot encode a None value. Ensure the object has an ID.")
        if not isinstance(number, int):
            raise TypeError(f"Expected int, got {type(number).__name__}")
        if number < 0:
            raise ValueError("Number must be a positive integer")
        return ShortCodeService._hashids.encode(number)

    @staticmethod
    def decode(code: str) -> int | None:
        decoded = ShortCodeService._hashids.decode(code)
        return decoded[0] if decoded else None


class UrlSequenceService:
    @staticmethod
    @transaction.atomic
    def next() -> int:
        from apps.converter.models import UrlSequence
        
        seq, _ = (
            UrlSequence.objects
            .select_for_update()
            .get_or_create(defaults={"value": 0})
        )

        seq.value = F("value") + 1
        seq.save(update_fields=["value"])

        seq.refresh_from_db(fields=["value"])
        return seq.value