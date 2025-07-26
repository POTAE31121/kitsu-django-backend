# =======================================================
#           menu/views.py (Final & Organized)
# =======================================================

import os
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


# =======================================================
#               HELPER FUNCTIONS
# =======================================================

def send_telegram_notification(order):
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')

    if not bot_token or not chat_id:
        print("WARNING: Telegram credentials not found. Skipping notification.")
        return

    message_items = "\n*Items:*\n"
    for item in order.items.all():
        # --- Bugfix: แก้ไขการ escape ตัวอักษรพิเศษสำหรับ MarkdownV2 ---
        item_name = item.menu_item_name.replace('-', '\\-').replace('.', '\\.').replace('!', '\\!').replace('(', '\\(').replace(')', '\\)')
        message_items += f"- {item_name} \\(x{item.quantity}\\)\n"

    # Build the full message with Markdown
    # --- Bugfix: แก้ไขการ escape ตัวอักษรพิเศษสำหรับ MarkdownV2 ---
    customer_name = order.customer_name.replace('-', '\\-').replace('.', '\\.').replace('!', '\\!').replace('(', '\\(').replace(')', '\\)')
    customer_phone = order.customer_phone.replace('-', '\\-').replace('.', '\\.').replace('!', '\\!').replace('(', '\\(').replace(')', '\\)')
    customer_address = order.customer_address.replace('-', '\\-').replace('.', '\\.').replace('!', '\\!').replace('(', '\\(').replace(')', '\\)')
    total_price = f"{order.total_price:.2f}".replace('.', '\\.')


    message = (
        f"🔔 *Kitsu Kitchen: New Order\\!* \n\n"
        f"*Order ID:* `{order.id}`\n"
        f"*Customer:* {customer_name}\n"
        f"*Phone:* {customer_phone}\n"
        f"*Address:* {customer_address}\n\n"
        f"*Total:* `{total_price}` *บาท*\n"
        f"{message_items}"
    )
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'MarkdownV2' # Using V2 for better compatibility
    }

    try:
        response = requests.post(url, json=payload, timeout=5) # --- Bugfix: เปลี่ยน data เป็น json ---
        response.raise_for_status()
        print("Telegram Notification sent successfully!")
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Could not send Telegram Notification: {e}")
        # --- Bugfix: พิมพ์เนื้อหาของ error ที่ได้จาก Telegram ---
        if e.response:
            print(f"Telegram API Response: {e.response.text}")


# =======================================================
#                   API VIEWS
# =======================================================

class MenuItemListAPIView(generics.ListAPIView):
    """
    API view to retrieve a list of all available menu items.
    """
    queryset = MenuItem.objects.filter(is_available=True)
    serializer_class = MenuItemSerializer


@method_decorator(csrf_exempt, name='dispatch')
class CreateOrderAPIView(APIView):
    """
    API view to create a new order from cart data.
    """
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