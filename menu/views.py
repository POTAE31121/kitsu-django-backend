# =======================================================
#           menu/views.py (Final & Organized)
# =======================================================

import os
from django.shortcuts import get_object_or_404
import requests
import json
import uuid
import hmac
import hashlib

from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.utils import timezone
from django.db.models import Sum, Count
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse

from rest_framework import generics, status
from rest_framework.permissions import IsAdminUser, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from .models import MenuItem, Order, OrderItem
from .serializers import (
    MenuItemSerializer,
    OrderStatusSerializer,
    AdminOrderSerializer,
    OrderSlipUploadSerializer,
    FinalOrderSubmissionSerializer,
)

# =======================================================
#               HELPER FUNCTIONS
# =======================================================

def send_telegram_notification(order):
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

class OrderStatusAPIView(generics.RetrieveAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderStatusSerializer
    lookup_field = 'id'
    permission_classes = [AllowAny]  # No authentication required for checking order status


class OrderSlipUploadAPIView(generics.UpdateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSlipUploadSerializer
    lookup_field = 'id'
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def perform_update(self, serializer):
        order = serializer.save()
        order.status = 'AWAITING_PAYMENT'
        order.payment_status = 'UNPAID'
        order.save()

# =======================================================
#               ADMIN-FACING API VIEWS
# =======================================================

class AdminOrderListView(generics.ListAPIView):
    queryset = Order.objects.all().order_by('-created_at')
    serializer_class = AdminOrderSerializer
    permission_classes = [IsAdminUser]


class AdminUpdateOrderStatusView(APIView):
    permission_classes = [IsAdminUser]

    VALID_TRANSITIONS = {
        'AWAITING_PAYMENT': ['AWAITING_PAYMENT', 'CANCELED'],
        'PAID': ['PAID', 'CANCELED'],
        'AWAITING_PREPARATION': ['AWAITING_PREPARATION', 'CANCELED'],
        'PREPARING': ['PREPARING', 'CANCELED'],
        'READY_FOR_DELIVERY': ['READY_FOR_DELIVERY', 'CANCELED'],
        'OUT_FOR_DELIVERY': ['OUT_FOR_DELIVERY', 'CANCELED'],
        'COMPLETED': ['COMPLETED'],
        'CANCELED': ['CANCELED'],
    }
    def patch(self, request, id, *args, **kwargs):
            order = get_object_or_404(Order, id=id)
            new_status = request.data.get('status')

            if not new_status:
                return Response(
                    {'error': 'status is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            allowed = self.VALID_TRANSITIONS.get(order.status, [])

            if new_status not in allowed:
                return Response(
                    {
                        'error': f"Cannot transition from '{order.status}' to '{new_status}'",
                        'allowed': allowed
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            order.status = new_status
            order.save(update_fields=['status'])

            return Response(
                AdminOrderSerializer(order).data,
                status=status.HTTP_200_OK
            )
    
# =======================================================
#               Admin Order Allowed Transitions View
# =======================================================
class AdminAllowedStatusTransitionsView(APIView):
    permission_classes = [IsAdminUser]

    VALID_TRANSITIONS = {
        'AWAITING_PAYMENT': ['PAID', 'CANCELED'],
        'PAID': ['AWAITING_PREPARATION', 'CANCELED'],
        'AWAITING_PREPARATION': ['PREPARING', 'CANCELED'],
        'PREPARING': ['READY_FOR_DELIVERY', 'CANCELED'],
        'READY_FOR_DELIVERY': ['OUT_FOR_DELIVERY', 'CANCELED'],
        'OUT_FOR_DELIVERY': ['COMPLETED', 'CANCELED'],
        'COMPLETED': [],
        'CANCELED': [],
    }

    def get(self, request, id, *args, **kwargs):
        order = get_object_or_404(Order, id=id)
        allowed = self.VALID_TRANSITIONS.get(order.status, [])
        return Response({
            'order_id': order.id,
            'current_status': order.status,
            'allowed_transitions': allowed
        })

# =======================================================
#               ADMIN DASHBOARD STATS API VIEW (FIXED)
# =======================================================
class AdminDashboardStatsAPIView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, *args, **kwargs):
        try:
            # ใช้วิธีที่ถูกต้องและปลอดภัยที่สุดในการจัดการ Timezone
            today = timezone.localtime(timezone.now()).date()

            # 1. หาออเดอร์ทั้งหมดของ "วันนี้" (ตามเวลาประเทศไทย)
            all_todays_orders = Order.objects.filter(created_at__date=today)
            # 2. หา 'เฉพาะ' ออเดอร์ที่เสร็จสมบูรณ์แล้วของวันนี้
            completed_todays_orders = all_todays_orders.filter(status='COMPLETED')

            # คำนวณยอดขาย
            todays_revenue = completed_todays_orders.aggregate(total=Sum('total_price'))['total'] or Decimal('0.00')
            # นับจำนวนออเดอร์ทั้งหมด
            total_orders_count = Order.objects.count()
            # นับจำนวนออเดอร์ของวันนี้
            todays_orders_count = all_todays_orders.count()

            data = {
                'todays_revenue': f"{todays_revenue:.2f}",
                'todays_orders_count': todays_orders_count,
                'total_orders_count': total_orders_count,
            }
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            # เพิ่มการดักจับ Error เพื่อให้เราเห็นว่าเกิดอะไรขึ้น
            print(f"ERROR in AdminDashboardStatsView: {e}")
            return Response(
                {"error": "An internal error occurred while calculating stats."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# =======================================================
class FinalOrderSubmissionAPIView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = FinalOrderSubmissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # 1. Parse items (FIX: validate structure ชัดเจน)
        try:
            items_data = json.loads(data['items'])
            if not isinstance(items_data, list) or not items_data:
                raise ValueError
        except (json.JSONDecodeError, ValueError):
            return Response(
                {'error': 'items must be a non-empty JSON array'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. Validate item ids (FIX: กัน id หาย)
        item_ids = []
        for item in items_data:
            if 'id' not in item or 'quantity' not in item:
                return Response(
                    {'error': 'Each item must contain id and quantity'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            item_ids.append(item['id'])

        # 3. Fetch menu items
        menu_items = MenuItem.objects.filter(id__in=item_ids)
        menu_map = {item.id: item for item in menu_items}

        if len(menu_map) != len(item_ids):
            return Response(
                {'error': 'Some menu items were not found'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 4. Create order (FIX: payment_slip optional)
        order = Order.objects.create(
            customer_name=data['customer_name'],
            customer_phone=data['customer_phone'],
            customer_address=data['customer_address'],
            payment_slip=data.get('payment_slip'),  # ← FIX สำคัญ
            status='AWAITING_PAYMENT',
            payment_status='UNPAID',
            total_price=Decimal('0.00')
        )

        # 5. Create order items + calculate total
        total_price = Decimal('0.00')
        order_items = []

        for item in items_data:
            try:
                menu_item = menu_map[item['id']]
                quantity = int(item['quantity'])
                if quantity <= 0:
                    raise ValueError
            except (KeyError, ValueError, TypeError):
                return Response(
                    {'error': 'Invalid item structure'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            total_price += menu_item.price * quantity

            order_items.append(
                OrderItem(
                    order=order,
                    menu_item=menu_item,
                    menu_item_name=menu_item.name,
                    quantity=quantity,
                    price=menu_item.price
                )
            )

        OrderItem.objects.bulk_create(order_items)

        # 6. Finalize order
        order.total_price = total_price
        order.save(update_fields=['total_price'])

        # 7. Notify AFTER commit (FIX: ไม่ rollback เพราะ Telegram)
        transaction.on_commit(lambda: send_telegram_notification(order))

        return Response(
            {
                'message': 'Order created successfully',
                'order_id': order.id,
                'total_price': f"{total_price:.2f}"
            },
            status=status.HTTP_201_CREATED
        )
    
# =======================================================
#               CREATE PAYMENT INTENT (FIXED)
# =======================================================
class CreatePaymentIntentAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        order_id = request.data.get('order_id')

        if not order_id:
            return Response(
                {'error': 'order_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return Response(
                {'error': 'order not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # ใช้เวลาไทยจริง
        now = timezone.localtime()

        intent_id = (
            f"KT-{now:%Y%m%d}-{now:%H%M%S}-"
            f"{uuid.uuid4().hex[:6].upper()}"
        )

        # bind intent_id กับ Order
        order.payment_intent_id = intent_id
        order.payment_status = 'UNPAID'
        order.status = 'AWAITING_PAYMENT'
        order.save(update_fields=[
            'payment_intent_id',
            'payment_status',
            'status'
        ])

        simulator_url = (
            "https://potae31121.github.io/kitsu-cloud-kitchen/"
            "payment-simulator.html"
            f"?intent_id={intent_id}"
            f"&amount={order.total_price:.2f}"
        )

        return Response({
            "order_id": order.id,
            "intent_id": intent_id,
            "amount": f"{order.total_price:.2f}",
            "simulator_url": simulator_url
        }, status=status.HTTP_200_OK)

# =======================================================
#           PAYMENT STATUS (POLLING)
# =======================================================

class PaymentStatusAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, payment_intent_id):
        try:
            order = Order.objects.get(payment_intent_id=payment_intent_id)
        except Order.DoesNotExist:
            return Response(
                {'error': 'Order not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response({
            'order_id': order.id,
            'payment_status': order.payment_status,
            'order_status': order.status,
        }, status=status.HTTP_200_OK)
