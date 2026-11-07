import logging
from django.db import transaction
from django.utils import timezone
from apps.core.models.audit import AuditTrailEvent
from apps.core.models.outbox import OutboxEvent
from apps.ncr.models.ncr import (
    NonConformanceReport,
    NcrStatus,
)

logger = logging.getLogger(__name__)


@transaction.atomic
def declare_quality_hold(
    source_domain: str,
    severity: str,
    target_type: str,
    target_identifier: str,
    defect_description: str,
    containment_actions: str,
    user=None,
    badge_number: str = "",
) -> NonConformanceReport:
    """
    Declares an Enterprise Quality Hold on a material lot, machine run, or finished goods pallet.
    Broadcasts multi-system quarantine signal via Transactional Outbox and seals 21 CFR 11 audit event.
    """
    effective_badge = badge_number or (getattr(user, "badge_number", "") if user else "") or "SYSTEM-QA"

    ncr = NonConformanceReport.objects.create(
        source_domain=source_domain,
        severity=severity,
        target_type=target_type,
        target_identifier=target_identifier,
        defect_description=defect_description,
        containment_actions=containment_actions,
        hold_declared=True,
        status=NcrStatus.OPEN_CONTAINED,
        created_by=user if getattr(user, "is_authenticated", False) else None,
    )

    payload = {
        "ncr_id": str(ncr.id),
        "ncr_number": ncr.ncr_number,
        "source_domain": ncr.source_domain,
        "severity": ncr.severity,
        "target_type": ncr.target_type,
        "target_identifier": ncr.target_identifier,
        "hold_declared": True,
        "status": ncr.status,
        "defect_description": ncr.defect_description,
        "containment_actions": ncr.containment_actions,
        "declared_by_badge": effective_badge,
        "timestamp": timezone.now().isoformat(),
    }

    # 1. Transactional Outbox for multi-system broadcast (WMS picking lock, MES hopper lock)
    OutboxEvent.objects.create(
        event_type="qms.quality_hold_declared",
        destination_system="ALL",
        payload=payload,
    )

    # 2. 21 CFR Part 11 Audit Trail event
    AuditTrailEvent.objects.create(
        action_type="QUALITY_HOLD_DECLARED",
        entity_type="NonConformanceReport",
        entity_id=ncr.id,
        badge_number=effective_badge,
        payload_snapshot=payload,
        signature_manifestation=f"Quality Hold Declared by {effective_badge} for {ncr.ncr_number}",
    )

    logger.warning(
        "Quality Hold declared: NCR=%s, Target=%s:%s, Severity=%s",
        ncr.ncr_number,
        ncr.target_type,
        ncr.target_identifier,
        ncr.severity,
    )

    return ncr


@transaction.atomic
def close_ncr(
    ncr: NonConformanceReport,
    resolution_notes: str,
    user=None,
    badge_number: str = "",
) -> NonConformanceReport:
    """
    Closes an NCR following successful corrective action or containment verification.
    """
    effective_badge = badge_number or (getattr(user, "badge_number", "") if user else "") or "SYSTEM-QA"

    ncr.status = NcrStatus.CLOSED
    ncr.containment_actions = f"{ncr.containment_actions}\n[Resolution]: {resolution_notes}".strip()
    ncr.save(update_fields=["status", "containment_actions", "updated_at"])

    payload = {
        "ncr_id": str(ncr.id),
        "ncr_number": ncr.ncr_number,
        "status": ncr.status,
        "resolution_notes": resolution_notes,
        "closed_by_badge": effective_badge,
        "timestamp": timezone.now().isoformat(),
    }

    OutboxEvent.objects.create(
        event_type="qms.ncr_closed",
        destination_system="ALL",
        payload=payload,
    )

    AuditTrailEvent.objects.create(
        action_type="UPDATE",
        entity_type="NonConformanceReport",
        entity_id=ncr.id,
        badge_number=effective_badge,
        payload_snapshot=payload,
        signature_manifestation=f"NCR {ncr.ncr_number} closed by {effective_badge}",
    )

    return ncr
