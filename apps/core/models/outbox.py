import uuid
from django.db import models
from django.utils import timezone


class OutboxStatusChoices(models.TextChoices):
    PENDING = "PENDING", "Pending Dispatch"
    DELIVERED = "DELIVERED", "Delivered Successfully"
    FAILED_RETRYING = "FAILED_RETRYING", "Failed, Pending Retry"
    EXHAUSTED = "EXHAUSTED", "Retries Exhausted / Alert Raised"


class OutboxEvent(models.Model):
    """
    Transactional Outbox Table for guaranteed at-least-once event delivery to MES, WMS, and ERP.
    Persisted atomically in the same database transaction as the business operation.
    """
    id = models.BigAutoField(primary_key=True)
    event_uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    event_type = models.CharField(
        max_length=100,
        db_index=True,
        help_text="e.g. qms.quality_hold_declared, qms.lot_released, qms.fai_released"
    )
    destination_system = models.CharField(
        max_length=50,
        db_index=True,
        help_text="Target system: WMS, MES, ERP"
    )
    payload = models.JSONField(help_text="Full serialized event payload matching canonical contract.")
    status = models.CharField(
        max_length=50,
        choices=OutboxStatusChoices.choices,
        default=OutboxStatusChoices.PENDING,
        db_index=True
    )
    retry_count = models.IntegerField(default=0)
    next_retry_at = models.DateTimeField(null=True, blank=True, db_index=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        db_table = "outbox_events"
        verbose_name = "Outbox Event"
        verbose_name_plural = "Outbox Events"
        ordering = ["id"]
        indexes = [
            models.Index(fields=["status", "next_retry_at"], name="idx_outbox_pending_retry"),
        ]

    def __str__(self):
        return f"[{self.status}] {self.event_type} -> {self.destination_system} ({self.event_uuid})"
