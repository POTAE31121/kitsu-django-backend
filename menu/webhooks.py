# menu/webhooks.py

import json
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status

from .models import Order
from .views import send_telegram_notification


# =======================================================
# Simulator Webhook (ใช้กับ payment-simulator.html)
# =======================================================

@method_decorator(csrf_exempt, name='dispatch')
class SimulatorWebhookAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            payload = json.loads(request.body)
        except json.JSONDecodeError:
            return Response({'error': 'Invalid JSON'}, status=400)
        
        print("DEBUG.PAYLOAD:", payload)

        intent_id = payload.get('intent_id')
        payment_status = payload.get('status')

        print("DEBUG.INTENT_ID:", intent_id)
        print("DEBUG.PAYMENT_STATUS:", payment_status)

        if not intent_id or not payment_status:
            return Response({'error': 'Invalid payload'}, status=400)

        try:
            order = Order.objects.select_for_update().get(
                payment_intent_id=intent_id
            )
            print("DEBUG order found:", order.id, order.payment_status)
        except Order.DoesNotExist:
            print("DEBUG order not found for intent_id:", intent_id)
            return Response({'error': 'Order not found'}, status=404)

        if order.payment_status == 'PAID':
            return Response({'message': 'Already processed'}, status=200)

        if payment_status == 'success':
            order.payment_status = 'PAID'
            order.status = 'PREPARING'
            order.paid_at = timezone.now()
            order.save()
            print("DEBUG order saved successfully")
            send_telegram_notification(order)
            return Response({'message': 'Payment confirmed'}, status=200)

        order.payment_status = 'FAILED'
        order.save()
        return Response({'message': 'Payment failed'}, status=200)


# =======================================================
# Stripe Webhook (placeholder – พร้อมต่อ Stripe จริง)
# =======================================================

@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # TODO: verify Stripe signature
        return Response(
            {'message': 'Stripe webhook received'},
            status=status.HTTP_200_OK
        )


# =======================================================
# Omise Webhook (placeholder – พร้อมต่อ Omise จริง)
# =======================================================

@method_decorator(csrf_exempt, name='dispatch')
class OmiseWebhookAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # TODO: verify Omise signature
        return Response(
            {'message': 'Omise webhook received'},
            status=status.HTTP_200_OK
        )
