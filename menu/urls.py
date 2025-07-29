# menu/urls.py (The Final, Correct Version)

from django.urls import path
from .views import (
    MenuItemListAPIView, 
    CreateOrderAPIView, 
    OrderStatusAPIView, 
    AdminOrderListView, 
    AdminUpdateOrderStatusView,
    AdminDashboardStatsAPIView,
    OrderSlipUploadAPIView,
    FinalOrderSubmissionAPIView,
)
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    # 1. เบอร์ต่อสำหรับ "ดึงรายการเมนู"
    path('items/', MenuItemListAPIView.as_view(), name='menu-item-list'),

    # 2. เบอร์ต่อสำหรับ "สร้างออเดอร์"
    path('orders/create/', CreateOrderAPIView.as_view(), name='create-order'),

    # 3. เบอร์ต่อสำหรับ "ติดตามสถานะออเดอร์"
    path('orders/<int:id>/', OrderStatusAPIView.as_view(), name='order-status'),

    # 4. เบอร์ต่อสำหรับ "รับโทเค็นการเข้าถึง"
    path('auth/token/', obtain_auth_token, name='api-token-auth'),\
    
    # 5. เบอร์ต่อสำหรับ "รายการออเดอร์สำหรับผู้ดูแลระบบ"
    path('admin/orders/', AdminOrderListView.as_view(), name='admin-order-list'),

    # 6. เบอร์ต่อสำหรับ "อัปเดตสถานะออเดอร์สำหรับผู้ดูแลระบบ"
    path('admin/orders/<int:id>/update-status/', AdminUpdateOrderStatusView.as_view(), name='admin-update-order-status'),

    # 7. เบอร์ต่อสำหรับ "สถิติแดชบอร์ดสำหรับผู้ดูแลระบบ"
    path('admin/stats/', AdminDashboardStatsAPIView.as_view(), name='admin-dashboard-stats'),

    # 8. เบอร์ต่อสำหรับ "อัปโหลดสลิปการชำระเงิน"
    path('orders/<int:id>/upload-slip/', OrderSlipUploadAPIView.as_view(), name='order-upload-slip'),

    # 9. เบอร์ต่อสำหรับ "ส่งออเดอร์สุดท้าย"
    path('orders/submit-final/', FinalOrderSubmissionAPIView.as_view(), name='final-order-submission'),
]