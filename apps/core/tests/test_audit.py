import uuid
import pytest
from django.db import IntegrityError
from apps.core.models import User, AuditTrailEvent, ActionTypeChoices, DepartmentChoices


@pytest.mark.django_db
class TestAuditTrailImmutability:
    def test_audit_event_hash_chain_creation(self):
        user = User.objects.create_user(
            username="qc_inspector_1",
            email="qc1@qms.plant",
            password="SecurePassword2026!",
            badge_number="BADGE-QC-001",
            department=DepartmentChoices.QC
        )

        # Create first audit event
        event1 = AuditTrailEvent.objects.create(
            user=user,
            badge_number=user.badge_number,
            client_ip="192.168.1.10",
            entity_type="Part",
            entity_id=uuid.uuid4(),
            action_type=ActionTypeChoices.CREATE,
            payload_snapshot={"part_number": "PRD-AUTO-BUMPER"},
            signature_manifestation="Inspector 1 - Created Part"
        )

        assert event1.record_hash is not None
        assert len(event1.record_hash) == 64
        assert event1.previous_record_hash == "0" * 64

        # Create second audit event (must chain to event1)
        event2 = AuditTrailEvent.objects.create(
            user=user,
            badge_number=user.badge_number,
            client_ip="192.168.1.10",
            entity_type="ControlPlan",
            entity_id=uuid.uuid4(),
            action_type=ActionTypeChoices.SIGN_OFF,
            payload_snapshot={"revision": "REV-A"},
            signature_manifestation="Inspector 1 - Signed Off"
        )

        assert event2.record_hash is not None
        assert len(event2.record_hash) == 64
        assert event2.previous_record_hash == event1.record_hash
        assert event2.record_hash != event1.record_hash

    def test_audit_event_update_raises_integrity_error(self):
        event = AuditTrailEvent.objects.create(
            badge_number="BADGE-001",
            entity_type="Part",
            action_type=ActionTypeChoices.CREATE,
            payload_snapshot={"test": 123}
        )

        with pytest.raises(IntegrityError):
            event.signature_manifestation = "Tampered Signature"
            event.save()

    def test_audit_event_delete_raises_integrity_error(self):
        event = AuditTrailEvent.objects.create(
            badge_number="BADGE-002",
            entity_type="Part",
            action_type=ActionTypeChoices.CREATE,
            payload_snapshot={"test": 456}
        )

        with pytest.raises(IntegrityError):
            event.delete()
