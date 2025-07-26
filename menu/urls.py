# menu/urls.py (The Final, Correct Version)

from django.urls import path
from .views import MenuItemListAPIView, CreateOrderAPIView, OrderStatusAPIView

urlpatterns = [
    # 1. เบอร์ต่อสำหรับ "ดึงรายการเมนู"
    path('items/', MenuItemListAPIView.as_view(), name='menu-item-list'),

    # 2. เบอร์ต่อสำหรับ "สร้างออเดอร์"
    path('orders/create/', CreateOrderAPIView.as_view(), name='create-order'),

    # 3. เบอร์ต่อสำหรับ "ติดตามสถานะออเดอร์"
    path('orders/<int:id>/', OrderStatusAPIView.as_view(), name='order-status'),
]