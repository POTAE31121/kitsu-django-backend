from django.test import TestCase
from rest_framework.test import APIClient
from decimal import Decimal
from .models import MenuItem, Order, OrderItem


class MenuItemAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        MenuItem.objects.create(
            name="ชุดข้าวเช้า",
            price=Decimal("120.00"),
            is_available=True
        )
        MenuItem.objects.create(
            name="ชุดเร่งด่วน",
            price=Decimal("100.00"),
            is_available=False
        )

    def test_get_menu_items_returns_only_available(self):
        """API ต้องคืนเฉพาะเมนูที่ is_available=True"""
        response = self.client.get('/api/items/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'ชุดข้าวเช้า')


class CreateOrderAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.menu_item = MenuItem.objects.create(
            name="ชุดพรีเมียม",
            price=Decimal("400.00"),
            is_available=True
        )

    def test_create_order_success(self):
        """สร้าง order สำเร็จ ต้องได้ order_id กลับมา"""
        payload = {
            "customer_name": "ทดสอบ",
            "customer_phone": "0812345678",
            "customer_address": "123 ถนนทดสอบ",
            "items": f'[{{"id": {self.menu_item.id}, "quantity": 2}}]'
        }
        response = self.client.post('/api/orders/submit-final/', payload, format='multipart')
        self.assertEqual(response.status_code, 201)
        self.assertIn('order_id', response.data)
        self.assertEqual(response.data['total_price'], '800.00')

    def test_create_order_empty_items_fails(self):
        """สร้าง order โดยไม่มี items ต้องได้ 400"""
        payload = {
            "customer_name": "ทดสอบ",
            "customer_phone": "0812345678",
            "customer_address": "123 ถนนทดสอบ",
            "items": "[]"
        }
        response = self.client.post('/api/orders/submit-final/', payload, format='multipart')
        self.assertEqual(response.status_code, 400)

    def test_create_order_invalid_menu_item_fails(self):
        """สร้าง order ด้วย menu item ที่ไม่มีในระบบ ต้องได้ 400"""
        payload = {
            "customer_name": "ทดสอบ",
            "customer_phone": "0812345678",
            "customer_address": "123 ถนนทดสอบ",
            "items": '[{"id": 9999, "quantity": 1}]'
        }
        response = self.client.post('/api/orders/submit-final/', payload, format='multipart')
        self.assertEqual(response.status_code, 400)


class OrderStatusAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.order = Order.objects.create(
            customer_name="ทดสอบ",
            customer_phone="0812345678",
            customer_address="123 ถนนทดสอบ",
            total_price=Decimal("400.00"),
            status="AWAITING_PAYMENT",
            payment_status="UNPAID"
        )

    def test_get_order_status_success(self):
        """ดึง order status ด้วย id ที่มีอยู่ ต้องได้ 200"""
        response = self.client.get(f'/api/orders/{self.order.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['payment_status'], 'UNPAID')

    def test_get_order_status_not_found(self):
        """ดึง order status ด้วย id ที่ไม่มี ต้องได้ 404"""
        response = self.client.get('/api/orders/9999/')
        self.assertEqual(response.status_code, 404)


class PaymentWebhookTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.order = Order.objects.create(
            customer_name="ทดสอบ",
            customer_phone="0812345678",
            customer_address="123 ถนนทดสอบ",
            total_price=Decimal("400.00"),
            status="AWAITING_PAYMENT",
            payment_status="UNPAID",
            payment_intent_id="KT-TEST-001"
        )

    def test_payment_success_updates_order(self):
        """webhook success ต้องเปลี่ยน status เป็น PAID และ PREPARING"""
        payload = {"intent_id": "KT-TEST-001", "status": "success"}
        response = self.client.post('/api/webhook/simulator/', payload, format='json')
        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, 'PAID')
        self.assertEqual(self.order.status, 'PREPARING')

    def test_payment_failed_updates_order(self):
        """webhook failed ต้องเปลี่ยน payment_status เป็น FAILED"""
        payload = {"intent_id": "KT-TEST-001", "status": "failed"}
        response = self.client.post('/api/webhook/simulator/', payload, format='json')
        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, 'FAILED')

    def test_payment_idempotency(self):
        """ยิง webhook ซ้ำบน order ที่ PAID แล้ว ต้องไม่เปลี่ยนแปลงอะไร"""
        self.order.payment_status = 'PAID'
        self.order.save()
        payload = {"intent_id": "KT-TEST-001", "status": "success"}
        response = self.client.post('/api/webhook/simulator/', payload, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['message'], 'Already processed')