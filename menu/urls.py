# menu/urls.py (The Final, Correct, Minimal Version)
from django.urls import path
from .views import MenuItemListAPIView, CreateOrderAPIView

urlpatterns = [
    path('items/', MenuItemListAPIView.as_view(), name='menu-item-list'),
    path('orders/create/', CreateOrderAPIView.as_view(), name='create-order'),
]