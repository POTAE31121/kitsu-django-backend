# =======================================================
#           menu/views.py (Final & Organized)
# =======================================================

import os
import requests
from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from django.db.models import Sum, Count
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from rest_framework import generics, status
from rest_framework.permissions import IsAdminUser, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser

from .models import MenuItem, Order, OrderItem
from .serializers import (
    MenuItemSerializer,
    OrderSerializer,
    OrderStatusSerializer,
    AdminOrderSerializer,
    OrderSlipUploadSerializer,
)

# =======================================================
#               HELPER FUNCTIONS
# =======================================================

def send_telegram_notification(order):
    """
    Sends a formatted plain text notification to a Telegram chat.
    """
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')

    if not bot_token or not chat_id:
        print("WARNING: Telegram credentials not found. Skipping notification.")
        return

    message_items = "\nItems:\n"
    for item in order.items.all():
        message_items += f"- {item.menu_item_name} (x{item.quantity})\n"

    message = (
        f"🔔 Kitsu Kitchen: New Order!\n\n"
        f"Order ID: {order.id}\n"
        f"Customer: {order.customer_name}\n"
        f"Phone: {order.customer_phone}\n"
        f"Address: {order.customer_address}\n\n"
        f"Total: {order.total_price:.2f} บาท\n"
        f"{message_items}"
    )
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': message,
    }

    try:
        response = requests.post(url, json=payload, timeout=5)
        response.raise_for_status()
        print("Telegram Notification sent successfully!")
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Could not send Telegram Notification: {e}")
        if e.response:
            print(f"Telegram API Response: {e.response.text}")


# =======================================================
#               CUSTOMER-FACING API VIEWS
# =======================================================

class MenuItemListAPIView(generics.ListAPIView):
    queryset = MenuItem.objects.filter(is_available=True)
    serializer_class = MenuItemSerializer
    permission_classes = [AllowAny] # No authentication required for menu items


@method_decorator(csrf_exempt, name='dispatch')
class CreateOrderAPIView(APIView):
    permission_classes = [AllowAny]  # No authentication required for creating orders
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = OrderSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        items_data = validated_data.pop('items')

        if not items_data:
            return Response({'error': 'Order must contain at least one item.'}, status=status.HTTP_400_BAD_REQUEST)

        # Efficiently fetch all menu items at once
        item_ids = [item_data['id'] for item_data in items_data]
        menu_items_in_db = MenuItem.objects.filter(id__in=item_ids)
        menu_items_map = {item.id: item for item in menu_items_in_db}

        if len(menu_items_map) != len(item_ids):
            missing_ids = set(item_ids) - set(menu_items_map.keys())
            return Response({'error': f"Menu items with ids {list(missing_ids)} not found."}, status=status.HTTP_400_BAD_REQUEST)

        # Create the main order record first
        order = Order.objects.create(total_price=0, **validated_data)
        
        order_items_to_create = []
        total_price = Decimal(0)

        for item_data in items_data:
            menu_item = menu_items_map.get(item_data['id'])
            price = menu_item.price
            quantity = item_data['quantity']
            total_price += price * quantity
            
            order_items_to_create.append(
                OrderItem(
                    order=order,
                    menu_item_name=menu_item.name,
                    quantity=quantity,
                    price=price
                )
            )

        OrderItem.objects.bulk_create(order_items_to_create)

        # Update the final total price
        order.total_price = total_price
        order.save()

        # Send notification AFTER the order is successfully saved
        send_telegram_notification(order)

        return Response({'message': 'Order created successfully!', 'order_id': order.id}, status=status.HTTP_201_CREATED)


class OrderStatusAPIView(generics.RetrieveAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderStatusSerializer
    lookup_field = 'id'
    permission_classes = [AllowAny]  # No authentication required for checking order status


class OrderSlipUploadAPIView(generics.UpdateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSlipUploadSerializer
    lookup_field = 'id'
    permission_classes = [AllowAny]  # Allow any user to upload payment slips
    parser_classes = [MultiPartParser, FormParser]

# =======================================================
#               ADMIN-FACING API VIEWS
# =======================================================

class AdminOrderListView(generics.ListAPIView):
    queryset = Order.objects.all().order_by('-created_at')
    serializer_class = AdminOrderSerializer
    permission_classes = [IsAdminUser]


class AdminUpdateOrderStatusView(APIView):
    permission_classes = [IsAdminUser]
    def patch(self, request, id, *args, **kwargs):
        try:
            order = Order.objects.get(id=id)
            new_status = request.data.get('status')
            
            valid_statuses = [choice[0] for choice in Order.STATUS_CHOICES]
            if new_status not in valid_statuses:
                return Response({'error': 'Invalid status provided.'}, status=status.HTTP_400_BAD_REQUEST)

            order.status = new_status
            order.save()
            return Response(AdminOrderSerializer(order).data, status=status.HTTP_200_OK)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)
        

# --- ⭐️ API View ใหม่สำหรับข้อมูลสรุปบน Dashboard (เวอร์ชันที่ถูกต้อง) ⭐️ ---
class AdminDashboardStatsView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, *args, **kwargs):
        now_utc = timezone.now()
        now_bkk = now_utc.astimezone(timezone.get_current_timezone())
        today = now_bkk.date()
        try:

            # 1. หาออเดอร์ทั้งหมดของวันนี้ (สำหรับนับจำนวน)
            all_todays_orders = Order.objects.filter(created_at__date=today)

            # 2. หา 'เฉพาะ' ออเดอร์ที่เสร็จสมบูรณ์แล้วของวันนี้ (สำหรับคำนวณยอดขาย)
            completed_todays_orders = all_todays_orders.filter(status='COMPLETED')

            # คำนวณยอดขายจากออเดอร์ที่เสร็จสมบูรณ์แล้วเท่านั้น
            todays_revenue = completed_todays_orders.aggregate(Sum('total_price'))['total_price__sum'] or 0

            # นับจำนวนออเดอร์ทั้งหมดในระบบ
            total_orders_count = Order.objects.count()

            # นับจำนวนออเดอร์ของวันนี้
            todays_orders_count = all_todays_orders.count()

            # เตรียมข้อมูลที่จะส่งกลับไป
            data = {
                'todays_revenue': f"{todays_revenue:.2f}",
                'todays_orders_count': todays_orders_count,
                'total_orders_count': total_orders_count,
            }
            return Response(data, status=status.HTTP_200_OK)
    
        except Exception as e:
            print(f"ERROR in AdminDashboardStatsAPIView: {e}")
            return Response(
            {'error': 'An error occurred while fetching dashboard stats.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    def get(self, request, *args, **kwargs):
        today = timezone.now().date()

         # --- ⭐️ การอัปเกรดสมองอยู่ตรงนี้ ⭐️ ---
        # 1. หาออเดอร์ทั้งหมดของวันนี้ (สำหรับนับจำนวน)
        all_todays_orders = Order.objects.filter(created_at__date=today)

        # 2. หาออเดอร์ที่มีสถานะ 'completed' ของวันนี้ (สำหรับนับรายได้)
        completed_todays_orders = all_todays_orders.filter(status='completed')  

        # 3. คำนวณรายได้รวมของออเดอร์ที่เสร็จสมบูรณ์
        total_revenue = completed_todays_orders.aggregate(Sum('total_price'))['total_price__sum'] or Decimal(0)

        # 4. นับจำนวนออเดอร์ทั้งหมดของวันนี้
        total_orders_today = all_todays_orders.count()

        # 5. นับจำนวนออเดอร์ที่เสร็จสมบูรณ์ของวันนี้
        completed_orders_today = completed_todays_orders.count()

        # 6. หา 5 เมนูที่ขายดีที่สุดของวันนี้
        popular_items = (
            OrderItem.objects.filter(order__created_at__date=today)
            .values('menu_item_name')
            .annotate(total_quantity=Sum('quantity'))
            .order_by('-total_quantity')[:5]
        )

        # 7. สร้างข้อมูลสรุป
        summary = {
            'total_revenue': f"{total_revenue:.2f} บาท",
            'total_orders_today': total_orders_today,
            'completed_orders_today': completed_orders_today,
            'popular_items': [
                {'name': item['menu_item_name'], 'quantity': item['total_quantity']}
                for item in popular_items
            ]
        }
        
    today = timezone.now().date()
    today_orders = Order.objects.filter(created_at__date=today)

    today_revenue = today_orders.aggregate(Sum('total_price'))['total_price__sum'] or Decimal(0)
    total_orders = Order.objects.count()
    today_order_count = today_orders.count()

    data = {
        'today_revenue': f"{today_revenue:.2f} บาท",
        'today_order_count': today_order_count,
        'total_orders': total_orders,
        'today_order_count': today_order_count,
        'popular_items': OrderItem.objects.filter(order__created_at__date=today)
            .values('menu_item_name')
            .annotate(total_quantity=Sum('quantity'))
            .order_by('-total_quantity')[:5],
    }