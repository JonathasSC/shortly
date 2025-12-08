import logging

from apps.billing.abstracts import PaymentAbstract

logger = logging.getLogger(__name__)

class MercadoPagoService(PaymentAbstract):
    def __init__(self, sdk):
        self.sdk = sdk

    def create_checkout_preference(
        self, title, price, quantity, back_urls, auto_return="approved", metadata=None
    ):
        logger.info(
            f"[MP][CREATE_PREFERENCE] Criando preferência | "
            f"title='{title}' price={price} qnt={quantity} metadata={metadata}"
        )

        preference_data = {
            "items": [
                {
                    "title": title,
                    "quantity": int(quantity),
                    "currency_id": "BRL",
                    "unit_price": float(price),
                }
            ],
            "back_urls": back_urls,
            "auto_return": auto_return,
        }

        if metadata:
            preference_data["metadata"] = {
                key: str(value) for key, value in metadata.items()
            }

        try:
            response = self.sdk.preference().create(preference_data)

            logger.info(
                f"[MP][CREATE_PREFERENCE] Resposta do MP | status={response.get('status')} "
                f"init_point={response.get('response', {}).get('init_point')}"
            )

            if response.get("status") != 201:
                logger.error(
                    f"[MP][CREATE_PREFERENCE] Falha inesperada | response={response}"
                )

            return response

        except Exception as e:
            logger.exception("[MP][CREATE_PREFERENCE] ERRO no request Mercado Pago")
            return {
                "status": 500,
                "response": {"error": str(e)},
            }
