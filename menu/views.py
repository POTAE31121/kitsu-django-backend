# menu/views.py (Final Correct Version)

from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import MenuItem, Order, OrderItem
from .serializers import MenuItemSerializer, OrderSerializer
from decimal import Decimal

# --- import ที่จำเป็น ---
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
# -----------------------------


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
                return Response({'error': f"Menu items with ids {', '.join(map(str, missing_ids))} not found."}, status=status.HTTP_400_BAD_REQUEST)

            order = Order.objects.create(
                total_price=0, # เริ่มต้นด้วย 0 ก่อน
                **validated_data
            )
            
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

            return Response({'message': 'Order created successfully!', 'order_id': order.id}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)