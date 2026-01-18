# menu/urls.py
from django.urls import path
from .views import (
    MenuItemListAPIView,
    OrderStatusAPIView,
    AdminOrderListView,
    AdminUpdateOrderStatusView,
    AdminDashboardStatsAPIView,
    OrderSlipUploadAPIView,
    FinalOrderSubmissionAPIView,
    CreatePaymentIntentAPIView,
    PaymentStatusAPIView,
)
from .webhooks import (
    SimulatorWebhookAPIView,
    StripeWebhookAPIView,
    OmiseWebhookAPIView,
)
from rest_framework.authtoken.views import obtain_auth_token


urlpatterns = [

    # Public
    path('items/', MenuItemListAPIView.as_view()),
    path('orders/<int:id>/', OrderStatusAPIView.as_view()),
    path('orders/<int:id>/upload-slip/', OrderSlipUploadAPIView.as_view()),
    path('orders/submit-final/', FinalOrderSubmissionAPIView.as_view()),

    # Payment
    path('payment/create-intent/', CreatePaymentIntentAPIView.as_view()),
    path('payment/status/<str:payment_intent_id>/', PaymentStatusAPIView.as_view()),

    # Webhooks (แยก provider)
    path('webhook/simulator/', SimulatorWebhookAPIView.as_view()),
    path('webhook/stripe/', StripeWebhookAPIView.as_view()),
    path('webhook/omise/', OmiseWebhookAPIView.as_view()),

    # Admin
    path('auth/token/', obtain_auth_token),
    path('admin/orders/', AdminOrderListView.as_view()),
    path('admin/orders/<int:id>/update-status/', AdminUpdateOrderStatusView.as_view()),
    path('admin/stats/', AdminDashboardStatsAPIView.as_view()),
]
