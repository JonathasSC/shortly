from django.urls import path
from .views import BuyCoinsPageView, SubscribePlanPageView, WalletPageView, BuyCoinsView, SubscribePlanView, MercadoPagoWebhookView
from django.http import HttpResponse


urlpatterns = [
    # ✅ Páginas (HTML)
    path('coins/', BuyCoinsPageView.as_view(), name='coins_page'),
    path('plans/', SubscribePlanPageView.as_view(), name='plans_page'),
    path('wallet/', WalletPageView.as_view(), name='wallet_page'),

    # ✅ Ações (checkout)
    path('buy-coins/<int:coin_amount>/',
         BuyCoinsView.as_view(), name='buy_coins'),
    path('subscribe/<int:plan_id>/',
         SubscribePlanView.as_view(), name='subscribe_plan'),
    path('mercado-pago/webhook/',
         MercadoPagoWebhookView.as_view(), name='mp_webhook'),

    # ✅ Páginas pós-pagamento
    path('payment/success/', lambda request: HttpResponse("Pagamento aprovado!"),
         name='payment_success'),
    path('payment/failure/', lambda request: HttpResponse("Pagamento falhou!"),
         name='payment_failure'),
]
