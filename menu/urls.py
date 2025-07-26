# menu/urls.py (The Final, Correct, Minimal Version)

from django.urls import path
from .views import MenuItemListAPIView, CreateOrderAPIView

urlpatterns = [
    # เส้นทางสำหรับดึงรายการเมนูทั้งหมด
    path('items/', MenuItemListAPIView.as_view(), name='menu-item-list'),

    # เส้นทางสำหรับสร้างออเดอร์ใหม่
    path('orders/create/', CreateOrderAPIView.as_view(), name='create-order'),
]