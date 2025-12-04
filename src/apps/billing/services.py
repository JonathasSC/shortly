from apps.billing.abstracts import PaymentAbstract


class MercadoPagoService(PaymentAbstract):
    def __init__(self, sdk):
        self.sdk = sdk

    def create_checkout_preference(
        self, title, price, quantity, back_urls, auto_return="approved", metadata=None
    ):
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
            return self.sdk.preference().create(preference_data)
        except Exception as e:
            return {"status": 500, "response": {"error": str(e)}}
