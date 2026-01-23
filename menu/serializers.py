# menu/serializers.py

from rest_framework import serializers
from .models import MenuItem, Order, OrderItem

class MenuItemSerializer(serializers.ModelSerializer):
    # --- เพิ่มบรรทัดนี้เข้ามาใหม่ ---
    # สร้างฟิลด์ใหม่ชื่อ image_url ที่จะเก็บ URL ฉบับเต็มของรูปภาพ
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = MenuItem
        # --- แก้ไข 'fields' ให้ใช้ 'image_url' แทน 'image' ---
        fields = ['id', 'name', 'description', 'price', 'image_url', 'is_available']

    # --- เพิ่มฟังก์ชันนี้เข้าไปใหม่ ---
    # นี่คือฟังก์ชันที่จะทำงานเพื่อสร้างค่าให้กับ 'image_url'
    def get_image_url(self, obj):
        # ถ้าเมนูชิ้นนั้นมีรูปภาพ (obj.image)
        try:
            if obj.image and hasattr(obj.image, 'url'):
            # ให้ return ค่า URL ฉบับเต็มออกมา
                return obj.image.url("http://", "https://")
            # ถ้าไม่มีรูปภาพ ก็ให้ return ค่าว่าง (None)
        except:
            return None
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