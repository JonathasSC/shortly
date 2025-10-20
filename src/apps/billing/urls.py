from django.http import HttpResponse
from django.urls import path

from apps.billing.views import (
    MercadoPagoWebhookView,
    SubscribePlanView,
    WalletPageView,
)

urlpatterns = [
    path('wallet/', WalletPageView.as_view(), name='wallet_page'),

    path('buy-coins/<int:coin_amount>/',
         WalletPageView.as_view(), name='buy_credits'),
    path('subscribe/<int:plan_id>/',
         SubscribePlanView.as_view(), name='subscribe_plan'),
    path('mercado-pago/webhook/',
         MercadoPagoWebhookView.as_view(), name='mp_webhook'),

    path('payment/success/', lambda request: HttpResponse("Pagamento aprovado!"),
         name='payment_success'),
    path('payment/failure/', lambda request: HttpResponse("Pagamento falhou!"),
         name='payment_failure'),
]
