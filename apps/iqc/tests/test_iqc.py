from decimal import Decimal
import pytest
from django.contrib.auth import get_user_model
from apps.core.models.outbox import OutboxEvent
from apps.master_data.models.material import ResinMaterial
from apps.iqc.models.iqc_task import IqcInspectionTask
from apps.iqc.services import (
    evaluate_coa_parameters,
    process_wms_inbound_shipment,
    submit_iqc_disposition,
)

User = get_user_model()


@pytest.fixture
def resin_abs(db):
    return ResinMaterial.objects.create(
        material_code="RES-ABS-HI",
        material_name="Starex ABS HF-0660I",
        polymer_type="ABS",
        supplier_code="VEND-LOTTE",
        target_moisture_max_pct=Decimal("0.0200"),
        target_mfi_nominal=Decimal("18.000"),
        target_mfi_tolerance=Decimal("2.000"),
    )


@pytest.fixture
def inspector_user(db):
    return User.objects.create_user(
        username="iqc_inspector_1",
        email="inspector1@qms.local",
        password="ValidPassword123!",
        badge_number="QA-IQC-001",
        department="QC",
    )


@pytest.mark.django_db
class TestIqcEvaluation:
    def test_coa_conforming_parameters(self, resin_abs):
        is_valid, issues = evaluate_coa_parameters(
            material=resin_abs,
            moisture_pct=Decimal("0.0150"),
            mfi_value=Decimal("18.500"),
            density=Decimal("1.0500"),
        )
        assert is_valid is True
        assert len(issues) == 0

    def test_coa_excessive_moisture_fails(self, resin_abs):
        is_valid, issues = evaluate_coa_parameters(
            material=resin_abs,
            moisture_pct=Decimal("0.0350"),
            mfi_value=Decimal("18.000"),
        )
        assert is_valid is False
        assert any("Moisture" in i for i in issues)

    def test_coa_mfi_out_of_tolerance_fails(self, resin_abs):
        is_valid, issues = evaluate_coa_parameters(
            material=resin_abs,
            moisture_pct=Decimal("0.0100"),
            mfi_value=Decimal("22.000"),  # allowable is 16 - 20
        )
        assert is_valid is False
        assert any("MFI" in i for i in issues)

    def test_process_wms_inbound_shipment_creates_task(self, resin_abs):
        payload = {
            "wms_event_id": "WMS-EVT-20261107-001",
            "material_code": "RES-ABS-HI",
            "lot_number": "LOT-ABS-202611-01",
            "supplier_code": "VEND-LOTTE",
            "quantity_kg": 5000.0,
            "pallet_barcodes": ["PAL-001", "PAL-002", "PAL-003"],
        }
        task = process_wms_inbound_shipment(payload)
        assert task.status == "PENDING_INSPECTION"
        assert task.lot_number == "LOT-ABS-202611-01"
        assert task.samples.count() == 3

        # Test idempotency on duplicate wms_event_id
        task_dup = process_wms_inbound_shipment(payload)
        assert task_dup.id == task.id
        assert IqcInspectionTask.objects.count() == 1

    def test_submit_iqc_acceptance_releases_to_wms(self, resin_abs, inspector_user):
        task = IqcInspectionTask.objects.create(
            wms_event_id="WMS-EVT-ACCEPT-01",
            lot_number="LOT-ABS-OK-01",
            material=resin_abs,
            supplier_code="VEND-LOTTE",
            quantity_kg=Decimal("2500.00"),
        )

        updated_task = submit_iqc_disposition(
            task=task,
            inspector=inspector_user,
            disposition="RELEASE_TO_AVAILABLE",
            coa_moisture=Decimal("0.0120"),
            coa_mfi=Decimal("17.800"),
            physical_moisture=Decimal("0.0110"),
            physical_mfi=Decimal("18.100"),
        )

        assert updated_task.status == "ACCEPTED"
        assert updated_task.disposition == "RELEASE_TO_AVAILABLE"

        # Check Outbox event emitted
        event = OutboxEvent.objects.filter(
            event_type="qms.lot_released",
            destination_system="WMS",
        ).first()
        assert event is not None
        assert event.payload["lot_number"] == "LOT-ABS-OK-01"
        assert event.payload["status"] == "AVAILABLE"
        assert event.payload["inspector_badge"] == "QA-IQC-001"

    def test_submit_iqc_rejection_emits_sncr(self, resin_abs, inspector_user):
        task = IqcInspectionTask.objects.create(
            wms_event_id="WMS-EVT-REJECT-01",
            lot_number="LOT-ABS-REJECT-01",
            material=resin_abs,
            supplier_code="VEND-LOTTE",
            quantity_kg=Decimal("1000.00"),
        )

        updated_task = submit_iqc_disposition(
            task=task,
            inspector=inspector_user,
            disposition="QUARANTINE_REJECTED",
            coa_moisture=Decimal("0.0450"),  # > 0.02%
            coa_mfi=Decimal("24.000"),
            rejection_reason="Excess moisture and high MFI beyond specification",
        )

        assert updated_task.status == "REJECTED"
        assert updated_task.disposition == "QUARANTINE_REJECTED"

        # Check SNCR Outbox event emitted
        event = OutboxEvent.objects.filter(
            event_type="qms.sncr_created",
            destination_system="WMS",
        ).first()
        assert event is not None
        assert event.payload["lot_number"] == "LOT-ABS-REJECT-01"
        assert event.payload["status"] == "QUARANTINE"
        assert "Excess moisture" in event.payload["rejection_reason"]
