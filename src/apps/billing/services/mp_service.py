import logging

from apps.billing.abstracts import PaymentAbstract
from apps.billing.dto import CheckoutPreferenceDTO
from apps.billing.models import UserSubscription

logger = logging.getLogger(__name__)


class MercadoPagoService(PaymentAbstract):
    def __init__(self, sdk):
        self.sdk = sdk

    def create_checkout_preference(self, data: CheckoutPreferenceDTO):
        logger.info(
            f"[MP][CREATE_PREFERENCE] Criando preferência | "
            f"title='{data.title}' price={data.price} qnt={data.quantity} metadata={data.metadata}"
        )

        preference_data = {
            "items": [
                {
                    "title": data.title,
                    "quantity": int(data.quantity),
                    "currency_id": "BRL",
                    "unit_price": float(data.price),
                }
            ],
            "back_urls": data.back_urls,
            "auto_return": data.auto_return,
        }

        if data.metadata:
            preference_data["metadata"] = {
                key: str(value) for key, value in data.metadata.items()
            }

        if data.notification_url:
            preference_data["notification_url"] = data.notification_url

        try:
            response = self.sdk.preference().create(preference_data)
            return response
        except Exception as e:
            logger.exception(
                "[MP][CREATE_PREFERENCE] ERRO no request Mercado Pago")
            return {
                "status": 500,
                "response": {"error": str(e)},
            }
