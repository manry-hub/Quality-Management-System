import pytest
from django.contrib.auth import get_user_model
from apps.core.models.audit import AuditTrailEvent
from apps.core.models.outbox import OutboxEvent
from apps.ncr.models.ncr import (
    SourceDomain,
    SeverityLevel,
    NcrStatus,
    TargetType,
)
from apps.ncr.services import declare_quality_hold, close_ncr

User = get_user_model()


@pytest.fixture
def qa_supervisor(db):
    user = User.objects.create_user(
        username="qa_supervisor_1",
        email="supervisor@qms.local",
        password="ValidPassword123!",
        badge_number="QA-SUP-001",
        department="QA",
    )
    return user


@pytest.mark.django_db
class TestNcrAndQualityHold:
    def test_declare_quality_hold_creates_ncr_and_events(self, qa_supervisor):
        ncr = declare_quality_hold(
            source_domain=SourceDomain.IQC,
            severity=SeverityLevel.CRITICAL,
            target_type=TargetType.MATERIAL_LOT,
            target_identifier="LOT-PP-202610-01",
            defect_description="Severe polymer moisture contamination (0.045% vs 0.015% max)",
            containment_actions="Segregated 5000kg in Warehouse Bay C-12, locked picking",
            user=qa_supervisor,
        )

        assert ncr.id is not None
        assert ncr.ncr_number.startswith("NCR-")
        assert ncr.hold_declared is True
        assert ncr.status == NcrStatus.OPEN_CONTAINED
        assert ncr.severity == SeverityLevel.CRITICAL

        # 1. Outbox Event verification
        outbox = OutboxEvent.objects.filter(
            event_type="qms.quality_hold_declared",
        ).order_by("-id").first()
        assert outbox is not None
        assert outbox.payload["ncr_number"] == ncr.ncr_number
        assert outbox.payload["target_identifier"] == "LOT-PP-202610-01"
        assert outbox.payload["hold_declared"] is True

        # 2. 21 CFR Part 11 Audit Trail event verification
        audit = AuditTrailEvent.objects.filter(
            entity_id=ncr.id,
            action_type="QUALITY_HOLD_DECLARED",
        ).first()
        assert audit is not None
        assert audit.badge_number == "QA-SUP-001"
        assert ncr.ncr_number in audit.signature_manifestation

    def test_close_ncr(self, qa_supervisor):
        ncr = declare_quality_hold(
            source_domain=SourceDomain.IPQC,
            severity=SeverityLevel.MINOR,
            target_type=TargetType.IN_PROCESS_RUN,
            target_identifier="IMM-02-RUN-104",
            defect_description="Minor flash on cavity 4",
            containment_actions="Adjusted clamping pressure",
            user=qa_supervisor,
        )

        closed_ncr = close_ncr(
            ncr=ncr,
            resolution_notes="Clamping pressure recalibrated to 180 bar. 3 sample shots within spec.",
            user=qa_supervisor,
        )

        assert closed_ncr.status == NcrStatus.CLOSED
        assert "Clamping pressure recalibrated" in closed_ncr.containment_actions

        # Outbox event
        outbox = OutboxEvent.objects.filter(
            event_type="qms.ncr_closed",
        ).first()
        assert outbox is not None
        assert outbox.payload["ncr_id"] == str(ncr.id)
        assert outbox is not None
