from django.db import transaction
from decimal import Decimal
from .models import Order, OrderItem, MenuItem

@transaction.atomic
def create_order(validated_data, items_data):

    item_ids = [item_data['id'] for item_data in items_data]
    menu_items_in_db = MenuItem.objects.filter(id__in=item_ids)
    menu_items_map = {item.id: item for item in menu_items_in_db}

    if len(menu_items_map) != len(item_ids):
        missing_ids = set(item_ids) - set(menu_items_map.keys())
        raise ValueError(f"Menu items with ids {list(missing_ids)} not found.")

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

    order.total_price = total_price
    order.save()

    return order
