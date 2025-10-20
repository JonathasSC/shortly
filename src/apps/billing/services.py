from apps.billing.abstracts import PaymentAbstract


class MercadoPagoService(PaymentAbstract):
    def __init__(self, sdk):
        self.sdk = sdk

    def create_checkout_preference(self, title, price, quantity, back_url_success, back_url_failure, metadata=None):
        preference_data = {
            "items": [
                {
                    "title": title,
                    "quantity": int(quantity),
                    "currency_id": "BRL",
                    "unit_price": float(price),
                }
            ],
            "back_urls": {
                "success": str(back_url_success),
                "failure": str(back_url_failure),
            },
        }

        if metadata:
            safe_metadata = {}
            for key, value in metadata.items():
                safe_metadata[key] = str(value)
            preference_data["metadata"] = safe_metadata

        try:
            response = self.sdk.preference().create(preference_data)
            return response
        except Exception as e:
            return {"status": 500, "response": {"error": str(e)}}
