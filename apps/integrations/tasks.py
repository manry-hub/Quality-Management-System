import logging
import requests
from celery import shared_task
from django.conf import settings
from django.db.models import Q as models_Q
from django.utils import timezone
from apps.core.models import OutboxEvent, OutboxStatusChoices

logger = logging.getLogger("qms.integrations.outbox")


@shared_task(bind=True, max_retries=5, default_retry_delay=10)
def relay_outbox_events(self):
    """
    Polls pending records in outbox_events table and dispatches HTTP webhooks to companion systems (MES / WMS).
    Implements exponential backoff and idempotency protection per ADR-002.
    """
    now = timezone.now()
    pending_events = OutboxEvent.objects.filter(
        status__in=[OutboxStatusChoices.PENDING, OutboxStatusChoices.FAILED_RETRYING]
    ).filter(
        models_Q(next_retry_at__isnull=True) | models_Q(next_retry_at__lte=now)
    ).order_by("id")[:50]

    dispatched_count = 0

    for event in pending_events:
        target_url = None
        headers = {
            "Content-Type": "application/json",
            "X-Idempotency-Key": str(event.event_uuid),
            "X-QMS-Event-Type": event.event_type,
        }

        if event.destination_system == "MES":
            target_url = f"{getattr(settings, 'MES_BASE_URL', 'http://mes:8080')}/api/v1/integration/qms/events"
            headers["Authorization"] = f"Bearer {getattr(settings, 'MES_SERVICE_TOKEN', '')}"
        elif event.destination_system == "WMS":
            target_url = f"{getattr(settings, 'WMS_BASE_URL', 'http://wms:8000')}/api/v1/integrations/qms/events"
            headers["X-WMS-Shared-Secret"] = getattr(settings, 'WMS_WEBHOOK_SECRET', '')

        if not target_url:
            event.status = OutboxStatusChoices.EXHAUSTED
            event.error_message = f"Unknown destination system: {event.destination_system}"
            event.save(update_fields=["status", "error_message"])
            continue

        try:
            response = requests.post(
                target_url,
                json=event.payload,
                headers=headers,
                timeout=5.0
            )
            if response.status_code in [200, 201, 202]:
                event.status = OutboxStatusChoices.DELIVERED
                event.delivered_at = timezone.now()
                event.error_message = ""
                event.save(update_fields=["status", "delivered_at", "error_message"])
                dispatched_count += 1
            else:
                _handle_failure(event, f"HTTP {response.status_code}: {response.text[:200]}")
        except Exception as exc:
            _handle_failure(event, str(exc))

    return f"Relayed {dispatched_count} events successfully."


def _handle_failure(event: OutboxEvent, error_msg: str):
    event.retry_count += 1
    event.error_message = error_msg
    if event.retry_count >= 5:
        event.status = OutboxStatusChoices.EXHAUSTED
        logger.critical(f"Outbox event {event.event_uuid} exhausted retries! Payload: {event.payload}")
    else:
        event.status = OutboxStatusChoices.FAILED_RETRYING
        # Exponential backoff: 10s, 30s, 90s, 270s
        delay_seconds = 10 * (3 ** (event.retry_count - 1))
        event.next_retry_at = timezone.now() + timezone.timedelta(seconds=delay_seconds)
    event.save(update_fields=["status", "retry_count", "error_message", "next_retry_at"])
