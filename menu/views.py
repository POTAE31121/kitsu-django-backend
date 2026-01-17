# =======================================================
#           menu/views.py (Final & Organized)
# =======================================================

import os
import requests
import json
import uuid
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
from rest_framework.parsers import MultiPartParser, FormParser

from .models import MenuItem, Order, OrderItem
from .serializers import (
    MenuItemSerializer,
    OrderSerializer,
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
    parser_classes = [MultiPartParser, FormParser]

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = FinalOrderSubmissionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        
        try:
            items_data = json.loads(validated_data['items'])
        except json.JSONDecodeError:
            return Response({'error': 'Invalid items format.'}, status=status.HTTP_400_BAD_REQUEST)

        # --- ที่เหลือคือ Logic การสร้าง Order ที่สมบูรณ์ ---
        total_price = Decimal(0)
        item_ids = [item['id'] for item in items_data]
        menu_items_in_db = MenuItem.objects.filter(id__in=item_ids)
        menu_items_map = {item.id: item for item in menu_items_in_db}

        if len(menu_items_map) != len(item_ids):
            return Response({'error': 'Some menu items were not found.'}, status=status.HTTP_400_BAD_REQUEST)

        order = Order.objects.create(
            customer_name=validated_data['customer_name'],
            customer_phone=validated_data['customer_phone'],
            customer_address=validated_data['customer_address'],
            payment_slip=validated_data['payment_slip'],
            total_price=0 # Start with 0
        )
        
        order_items_to_create = []
        for item_data in items_data:
            menu_item = menu_items_map.get(item_data['id'])
            price = menu_item.price
            quantity = item_data['quantity']
            total_price += price * quantity
            order_items_to_create.append(
                OrderItem(order=order, menu_item_name=menu_item.name, quantity=quantity, price=price)
            )

        OrderItem.objects.bulk_create(order_items_to_create)
        order.total_price = total_price
        order.save()
        
        send_telegram_notification(order)
        return Response({'message': 'Order created successfully!', 'order_id': order.id}, status=status.HTTP_201_CREATED)
    
# =======================================================
#               CREATE PAYMENT INTENT
# =======================================================
class CreatePaymentIntentAPIView(APIView):
    permission_classes = [AllowAny]

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        amount = request.data.get('amount')
        if not amount:
            return Response({'error': 'Amount is required.'}, status=400)

        try:
            amount_decimal = Decimal(amount)
            if amount_decimal <= 0:
                raise ValueError
        except:
            return Response({'error': 'Invalid amount.'}, status=400)

        # ❌ Stripe ยังไม่ใช้ → mock intent
        payment_intent_id = f"pi_{uuid.uuid4().hex}"

        simulator_url = (
            f"https://potae31121.github.io/kitsu-cloud-kitchen/"
            f"payment-simulator.html"
            f"?intent_id={payment_intent_id}"
            f"&amount={amount_decimal}"
        )

        return Response({
            "simulator_url": "https://kitsu-backend.onrender.com/payment-simulator.html"
        }, status=status.HTTP_200_OK)

class PaymentWebhookAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        payload = request.data
        # Verify the webhook signature (if using Stripe, for example)
        # Handle the event (e.g., payment succeeded, payment failed)
        intent_id = request.data.get('intent_id')
        event_type = request.data.get('event_type')

        try:
            order = Order.objects.get(payment_intent_id=intent_id)
            if event_type == 'payment.success':
                order.status = 'PREPARING'
                order.save()
                send_telegram_notification(order)
                return Response({'status': 'success'}, status=status.HTTP_200_OK)
            else:
                order.status = 'CANCELLED' # ถ้าจ่ายล้มเหลว
                order.save()
                return Response({'status': 'failed'}, status=status.HTTP_200_OK)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)