import logging

from apps.billing.abstracts import PaymentAbstract
from apps.billing.models import UserWallet, WalletTransaction, UserSubscription
from django.db import transaction

logger = logging.getLogger(__name__)

class MercadoPagoService(PaymentAbstract):
    def __init__(self, sdk):
        self.sdk = sdk

    def create_checkout_preference(
        self, title, price, quantity, back_urls, auto_return="approved", metadata=None, notification_url=None
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

        if notification_url:
            preference_data["notification_url"] = notification_url
            logger.info(f"[MP][CREATE_PREFERENCE] Notification URL registrada: {notification_url}")

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
            
            
class WalletCreditService:

    @staticmethod
    def apply_credit(user_id, amount, payment_id):
        wallet, _ = UserWallet.objects.get_or_create(user_id=user_id)

        if WalletTransaction.objects.filter(external_reference=payment_id).exists():
            return

        with transaction.atomic():
            wallet.credit(amount)
            WalletTransaction.objects.create(
                wallet=wallet,
                amount=amount,
                transaction_type="credit",
                external_reference=payment_id,
            )
            
class SubscriptionService:
    @staticmethod
    def activate(user_id, plan_id):
        UserSubscription.objects.update_or_create(
            user_id=user_id, defaults={"plan_id": plan_id, "is_active": True}
        )
