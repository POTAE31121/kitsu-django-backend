# menu/serializers.py

from rest_framework import serializers
from .models import MenuItem

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
        if obj.image and hasattr(obj.image, 'url'):
            # ให้ return ค่า URL ฉบับเต็มออกมา
            return obj.image.url
        # ถ้าไม่มีรูปภาพ ก็ให้ return ค่าว่าง (None)
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

# ... (ต่อท้ายไฟล์) ...
class OrderStatusSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True) # ใช้ OrderItemSerializer เดิม

    class Meta:
        model = Order # type: ignore
        fields = ['id', 'status', 'created_at', 'total_price', 'items']