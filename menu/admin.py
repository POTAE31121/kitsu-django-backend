# menu/admin.py (Correct Final Version)
from django.contrib import admin
from .models import MenuItem, Order, OrderItem
from django.utils.html import format_html

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ('menu_item_name', 'quantity', 'price')
    readonly_fields = fields
    can_delete = False
    def has_add_permission(self, request, obj=None):
        return False

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_name', 'customer_phone', 'status', 'total_price', 'created_at', 'payment_status')
    list_filter = ('status', 'payment_status', 'created_at')
    search_fields = ('customer_name', 'customer_phone', 'customer_address', 'payment_intent_id')
    list_editable = ('status',)
    inlines = [OrderItemInline]
    readonly_fields = ('customer_name', 'customer_phone', 'customer_address', 'total_price', 'created_at', 'payment_slip_thumbnail')

    def payment_slip_thumbnail(self, obj):
        if obj.payment_slip:
            return format_html('<img src="{}" style="max-height: 100px; max-width: 100px;" />', obj.payment_slip.url)
        return "No Slip"
    payment_slip_thumbnail.short_description = 'Payment Slip'

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'is_available')
    list_editable = ('is_available',)