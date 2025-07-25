# menu/urls.py
from django.urls import path # type: ignore
from .views import MenuItemListAPIView, CreateOrderAPIView

urlpatterns = [
    path('items/', MenuItemListAPIView.as_view(), name='menu-item-list'),
    path('orders/create/', CreateOrderAPIView.as_view(), name='create-order'), # เพิ่มบรรทัดนี้
]