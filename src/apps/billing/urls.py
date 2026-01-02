from django.urls import path

from apps.billing.views import (
    BuyCoinsView,
    PaymentFailureView,
    PaymentPendingView,
    PaymentStatusAPI,
    PaymentSuccessView,
    WalletPageView,
)
from apps.billing.webhook import MercadoPagoWebhookView

urlpatterns = [
    path('wallet/', WalletPageView.as_view(), name='wallet_page'),

    path('buy-coins/<int:credit_amount>/',
         BuyCoinsView.as_view(), name='buy_credits'),

    path('mercado-pago/webhook/',
         MercadoPagoWebhookView.as_view(), name='mp_webhook'),

    path('payment/success/',
         PaymentSuccessView.as_view(), name='payment_success'),
    path('payment/failure/',
         PaymentFailureView.as_view(), name='payment_failure'),
    path('payment/pending/',
         PaymentPendingView.as_view(), name='payment_pending'),

    path("payment/status/", PaymentStatusAPI.as_view(), name="payment_status_api"),
]
