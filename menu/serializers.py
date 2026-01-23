# menu/serializers.py

from rest_framework import serializers
from .models import MenuItem, Order, OrderItem

class MenuItemSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = MenuItem
        fields = ['id', 'name', 'description', 'price', 'image_url', 'is_available']

    def get_image_url(self, obj):
        # ถ้าเมนูชิ้นนั้นมีรูปภาพ (obj.image)
        if obj.image:
            return obj.image.url
        return None
# ... ต่อท้ายคลาส MenuItemSerializer ...

class OrderItemSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    quantity = serializers.IntegerField()

class OrderSerializer(serializers.Serializer):
    customer_name = serializers.CharField(max_length=100)
    customer_phone = serializers.CharField(max_length=20)
    customer_address = serializers.CharField()
    items = OrderItemSerializer(many=True)

# --- เพิ่ม Serializer ใหม่สำหรับหน้าติดตามออเดอร์ ---
class OrderStatusSerializer(serializers.ModelSerializer):
    # เราจะใช้ SerializerMethodField เพื่อให้เราควบคุมการแสดงผลได้ดีขึ้น
    items = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ['id', 'status', 'created_at', 'total_price', 'items']
    
    def get_items(self, obj):
        # ดึงข้อมูล OrderItem ทั้งหมดที่เกี่ยวข้องกับ Order นี้
        order_items = OrderItem.objects.filter(order=obj)
        # สร้างข้อมูลที่จะส่งกลับไป
        return [
            {
                'name': item.menu_item_name,
                'quantity': item.quantity,
                'price': f"{item.price:.2f}"
            }
            for item in order_items
        ]
# --- ต่อท้ายคลาส OrderStatusSerializer ---

# --- Serialirzer สำหรับแสดง OrderItem ในหน้า Dashboard ---
class OrderItemDashboardSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'menu_item_name', 'quantity', 'price']

# --- Serializer สำหรับแสดง Order ในหน้า Dashboard ---
class OrderDashboardSerializer(serializers.ModelSerializer):
    items = OrderItemDashboardSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'customer_name', 'customer_phone', 'customer_address', 'status', 'created_at', 'total_price', 'items']

class AdminOrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['menu_item_name', 'quantity', 'price']

class AdminOrderSerializer(serializers.ModelSerializer):
    items = AdminOrderItemSerializer(many=True, read_only=True)
    
    payment_slip_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = ['id', 'customer_name', 'customer_phone', 'customer_address', 'status', 'created_at', 'total_price', 'items', 'payment_slip_url']

    def get_payment_slip_url(self, obj):
        if obj.payment_slip and hasattr(obj.payment_slip, 'url'):
            return obj.payment_slip.url
        return None

class OrderSlipUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['payment_slip']

class FinalOrderSubmissionSerializer(serializers.Serializer):
    customer_name = serializers.CharField(max_length=100)
    customer_phone = serializers.CharField(max_length=20)
    customer_address = serializers.CharField()
    items = serializers.CharField() # เราจะรับ items เป็น JSON string
    payment_slip = serializers.ImageField(
        required=False,
        allow_null=True,
    )