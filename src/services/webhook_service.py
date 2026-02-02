import hmac
import hashlib
import httpx
from typing import Dict, Any, Optional
from datetime import datetime


class WebhookService:
    def __init__(self):
        self.timeout = 10

    def generate_signature(self, payload: str, secret_key: str) -> str:
        """Generate HMAC SHA256 signature for webhook payload"""
        return hmac.new(
            secret_key.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256
        ).hexdigest()

    async def send_webhook(
        self, url: str, payload: Dict[str, Any], secret_key: str, timeout: int = 10
    ) -> tuple[bool, Optional[int], Optional[str], Optional[str]]:
        """
        Send webhook to URL.

        Returns:
            (success, status_code, response_body, error_message)
        """
        import json

        payload_str = json.dumps(payload, default=str)
        signature = self.generate_signature(payload_str, secret_key)

        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Signature": signature,
            "X-Webhook-Timestamp": str(int(datetime.utcnow().timestamp())),
        }

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(url, json=payload, headers=headers)

                if response.status_code < 400:
                    return (True, response.status_code, response.text, None)
                else:
                    return (
                        False,
                        response.status_code,
                        response.text,
                        f"HTTP {response.status_code}",
                    )

        except httpx.TimeoutException:
            return (False, None, None, "Connection timeout")
        except httpx.RequestError as e:
            return (False, None, None, str(e))
        except Exception as e:
            return (False, None, None, f"Unexpected error: {str(e)}")

    def create_webhook_payload(
        self, event_type: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create standardized webhook payload"""
        return {
            "event": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }


# Singleton instance
webhook_service = WebhookService()
