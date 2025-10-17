import mercadopago
from django.conf import settings
from django.http import HttpResponse


class MercadoPagoService:
    def __init__(self):
        self.sdk = mercadopago.SDK(settings.MERCADO_PAGO_ACCESS_TOKEN)
        print(settings.MERCADO_PAGO_ACCESS_TOKEN)

    def create_checkout_preference(
        self,
        title: str,
        price: float,
        quantity: int = 1,
        back_url_success: str = None,
        back_url_failure: str = None,
        metadata: dict = None
    ) -> dict:
        preference_data = {
            "items": [
                {
                    "title": title,
                    "quantity": quantity,
                    "currency_id": "BRL",
                    "unit_price": float(price),
                }
            ],
            "back_urls": {
                "success": back_url_success,
                "failure": back_url_failure,
                "pending": back_url_success,
            },
            "auto_return": "approved",
            "metadata": metadata or {},
        }

        preference_response = self.sdk.preference().create(preference_data)
        return preference_response["response"]
