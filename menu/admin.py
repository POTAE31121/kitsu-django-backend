# menu/admin.py (Correct Final Version)
from django.contrib import admin
from .models import MenuItem, Order, OrderItem

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
    list_display = ('id', 'customer_name', 'customer_phone', 'status', 'total_price', 'created_at', 'is_completed')
    list_filter = ('status', 'is_completed', 'created_at')
    search_fields = ('customer_name', 'customer_phone')
    list_editable = ('status',)
    inlines = [OrderItemInline]
    readonly_fields = ('customer_name', 'customer_phone', 'customer_address', 'total_price', 'created_at')

admin.site.register(MenuItem)