import hashlib
import json
import uuid
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, IntegrityError
from django.utils import timezone


class ActionTypeChoices(models.TextChoices):
    CREATE = "CREATE", "Record Created"
    UPDATE = "UPDATE", "Record Updated / Addendum"
    SIGN_OFF = "SIGN_OFF", "Electronic Signature"
    DISPOSITION = "DISPOSITION", "Material Disposition"
    QA_HOLD = "QA_HOLD", "Quality Hold Declared"
    QA_RELEASE = "QA_RELEASE", "Quality Release Issued"
    CALIBRATION_LOCK = "CALIBRATION_LOCK", "Instrument Locked Out"


class AuditTrailEvent(models.Model):
    """
    21 CFR Part 11 & IATF 16949 Compliant Append-Only Cryptographic Audit Log.
    Each event is linked to the previous event via a SHA-256 Merkle hash chain.
    Direct UPDATE or DELETE operations are strictly forbidden.
    """
    id = models.BigAutoField(primary_key=True)
    event_uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_events",
        db_index=True
    )
    badge_number = models.CharField(max_length=50, blank=True, db_index=True)
    client_ip = models.GenericIPAddressField(null=True, blank=True)
    entity_type = models.CharField(max_length=100, db_index=True)
    entity_id = models.UUIDField(null=True, blank=True, db_index=True)
    action_type = models.CharField(max_length=50, choices=ActionTypeChoices.choices, db_index=True)
    payload_snapshot = models.JSONField(default=dict)
    signature_manifestation = models.CharField(max_length=255, blank=True)
    previous_record_hash = models.CharField(max_length=64, blank=True)
    record_hash = models.CharField(max_length=64, unique=True, db_index=True)

    class Meta:
        db_table = "audit_trail_events"
        verbose_name = "Audit Trail Event"
        verbose_name_plural = "Audit Trail Events"
        ordering = ["id"]

    def __str__(self):
        return f"[{self.timestamp.isoformat()}] {self.action_type} on {self.entity_type} ({self.record_hash[:8]}...)"

    def clean(self):
        if self.pk is not None:
            raise ValidationError("21 CFR Part 11: Existing audit trail records are strictly immutable.")

    def compute_hash(self, prev_hash: str) -> str:
        """
        Computes deterministic SHA-256 hash chaining:
        H_n = SHA-256(H_{n-1} || timestamp || user_id || entity_type || entity_id || payload || salt)
        """
        payload_str = json.dumps(self.payload_snapshot, sort_keys=True, default=str)
        user_str = str(self.user_id) if self.user_id else (self.badge_number or "SYSTEM")
        salt = getattr(settings, "AUDIT_TRAIL_SALT", "qms_merkle_default_salt_2026")

        hash_content = (
            f"{prev_hash}|"
            f"{self.timestamp.isoformat()}|"
            f"{user_str}|"
            f"{self.client_ip or ''}|"
            f"{self.entity_type}|"
            f"{str(self.entity_id or '')}|"
            f"{self.action_type}|"
            f"{self.signature_manifestation}|"
            f"{payload_str}|"
            f"{salt}"
        )
        return hashlib.sha256(hash_content.encode("utf-8")).hexdigest()

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise IntegrityError(
                "21 CFR Part 11 Violation: Modification of existing audit trail records is prohibited."
            )

        if not self.previous_record_hash:
            last_record = AuditTrailEvent.objects.order_by("-id").first()
            self.previous_record_hash = last_record.record_hash if last_record else ("0" * 64)

        if not self.record_hash:
            self.record_hash = self.compute_hash(self.previous_record_hash)

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise IntegrityError("21 CFR Part 11 Violation: Deletion of audit trail records is prohibited.")
