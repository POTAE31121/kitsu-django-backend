# =======================================================
#           menu/views.py (The Final, Correct Version)
# =======================================================

import os
import re
import requests
from decimal import Decimal

from django.db import transaction
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import MenuItem, Order, OrderItem
from .serializers import MenuItemSerializer, OrderSerializer

# --- 1. "เครื่องฆ่าเชื้อ" ที่แข็งแกร่งที่สุด ---
def escape_markdown_v2(text):
    """Escapes characters for Telegram's MarkdownV2 parser."""
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', str(text))

# --- 2. ฟังก์ชันส่ง Telegram ที่ใช้ "เครื่องฆ่าเชื้อ" ---
def send_telegram_notification(order):
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')

    if not bot_token or not chat_id:
        print("WARNING: Telegram credentials not found. Skipping notification.")
        return

    # สร้างข้อความแบบ Plain Text ที่ไม่มี Markdown
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
    # --- ลบ parse_mode ออกทั้งหมด ---
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

# --- 3. API Views (ไม่มีการแก้ไข) ---
class MenuItemListAPIView(generics.ListAPIView):
    queryset = MenuItem.objects.filter(is_available=True)
    serializer_class = MenuItemSerializer

@method_decorator(csrf_exempt, name='dispatch')
class CreateOrderAPIView(APIView):
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = OrderSerializer(data=request.data)
        if serializer.is_valid():
            validated_data = serializer.validated_data
            items_data = validated_data.pop('items')

            if not items_data:
                return Response({'error': 'Order must contain at least one item.'}, status=status.HTTP_400_BAD_REQUEST)

            total_price = Decimal(0)
            
            item_ids = [item_data['id'] for item_data in items_data]
            menu_items_in_db = MenuItem.objects.filter(id__in=item_ids)
            menu_items_map = {item.id: item for item in menu_items_in_db}

            if len(menu_items_map) != len(item_ids):
                missing_ids = set(item_ids) - set(menu_items_map.keys())
                return Response({'error': f"Menu items with ids {list(missing_ids)} not found."}, status=status.HTTP_400_BAD_REQUEST)

            order = Order.objects.create(total_price=0, **validated_data)
            
            order_items_to_create = []
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

            order.total_price = total_price
            order.save()

            # ส่งการแจ้งเตือนหลังจากบันทึกสำเร็จ
            send_telegram_notification(order)

            return Response({'message': 'Order created successfully!', 'order_id': order.id}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)