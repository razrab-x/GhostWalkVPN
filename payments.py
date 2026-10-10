import aiohttp
import hashlib
import hmac
import json
from config import (
    ROLLY_API_URL, ROLLY_TERMINAL_ID, ROLLY_API_KEY,
    ROLLY_SECRET, ROLLY_CALLBACK,
)

async def create_payment(amount: int, order_id: str, description: str) -> dict:
    payload = {
        "terminal_id": ROLLY_TERMINAL_ID,
        "order_id": order_id,
        "amount": amount,
        "currency": "RUB",
        "method": "sbp",
        "description": description,
        "callback_url": ROLLY_CALLBACK,
    }
    body = json.dumps(payload, separators=(",", ":"))
    sign = hmac.new(
        ROLLY_SECRET.encode(), body.encode(), hashlib.sha256
    ).hexdigest()

    headers = {
        "Authorization": f"Bearer {ROLLY_API_KEY}",
        "Content-Type": "application/json",
        "X-Signature": sign,
    }
    async with aiohttp.ClientSession() as s:
        async with s.post(f"{ROLLY_API_URL}/v1/payments", data=body, headers=headers) as r:
            return await r.json()

def verify_webhook(body: bytes, signature: str) -> bool:
    expected = hmac.new(
        ROLLY_SECRET.encode(), body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
