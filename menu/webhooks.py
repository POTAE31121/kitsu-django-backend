# menu/webhooks.py
import json
import hmac
import hashlib

from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction

from .models import Order


def verify_hmac(payload, signature):
    expected = hmac.new(
        settings.WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


@csrf_exempt
def simulator_webhook(request):
    payload = request.body
    signature = request.headers.get('X-Signature')

    if not verify_hmac(payload, signature):
        return HttpResponse(status=400)

    data = json.loads(payload)
    intent_id = data.get('payment_intent_id')

    if not intent_id:
        return HttpResponse(status=400)

    with transaction.atomic():
        try:
            order = Order.objects.select_for_update().get(
                payment_intent_id=intent_id
            )
        except Order.DoesNotExist:
            return HttpResponse(status=404)

        # 🔒 กันยิงซ้ำ
        if order.status in ['PAID', 'PREPARING', 'COMPLETED']:
            return HttpResponse(status=200)

        order.status = 'PAID'
        order.save()

    return HttpResponse(status=200)


# =========================
# Placeholder สำหรับของจริง
# =========================

@csrf_exempt
def stripe_webhook(request):
    # Stripe-Signature verify จะมาใส่ตรงนี้
    return HttpResponse(status=200)


@csrf_exempt
def omise_webhook(request):
    # Omise signature verify จะมาใส่ตรงนี้
    return HttpResponse(status=200)
