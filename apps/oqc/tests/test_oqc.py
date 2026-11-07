import pytest
from django.contrib.auth import get_user_model
from apps.core.models.outbox import OutboxEvent
from apps.master_data.models.part import Part
from apps.oqc.models.oqc_inspection import OqcInspection, OqcDefectItem
from apps.oqc.services import (
    get_iso2859_sample_size,
    evaluate_and_release_oqc,
)

User = get_user_model()


@pytest.fixture
def sample_part(db):
    return Part.objects.create(
        part_number="PRD-DOOR-TRIM",
        part_name="Front Left Door Trim Panel",
        drawing_number="DWG-TRIM-001",
        drawing_revision="REV-A",
        cavity_count=4,
        material_code="RES-PP-TD20",
    )


@pytest.fixture
def inspector_user(db):
    return User.objects.create_user(
        username="oqc_inspector_1",
        email="oqc1@qms.local",
        password="ValidPassword123!",
        badge_number="QA-OQC-003",
        department="QC",
    )


@pytest.mark.django_db
class TestOqcOperations:
    def test_iso2859_sample_size_calculator(self):
        assert get_iso2859_sample_size(5) == 2
        assert get_iso2859_sample_size(50) == 8
        assert get_iso2859_sample_size(500) == 50
        assert get_iso2859_sample_size(1000) == 80
        assert get_iso2859_sample_size(3000) == 125
        assert get_iso2859_sample_size(5000) == 200

    def test_oqc_zero_defect_release_generates_coc(self, sample_part, inspector_user):
        inspection = OqcInspection.objects.create(
            pallet_barcode="PAL-TRIM-202611-001",
            part=sample_part,
            batch_quantity=1000,
            sample_size=80,
            defects_found=0,
            packaging_box_intact=True,
            esd_bag_sealed=True,
            desiccant_present=True,
            datamatrix_verified=True,
        )

        released, coc_number, msg = evaluate_and_release_oqc(inspection, inspector_user)

        assert released is True
        assert coc_number.startswith("COC-")
        assert inspection.status == "RELEASED_FOR_SHIPMENT"
        assert inspection.coc_number == coc_number
        assert inspection.coc_file_path != ""

        event = OutboxEvent.objects.filter(
            event_type="qms.coc_released",
            destination_system="WMS",
        ).first()
        assert event is not None
        assert event.payload["pallet_barcode"] == "PAL-TRIM-202611-001"
        assert event.payload["coc_number"] == coc_number
        assert event.payload["status"] == "AVAILABLE_FOR_SHIPMENT"

    def test_oqc_defect_found_rejects_lot_c_zero(self, sample_part, inspector_user):
        inspection = OqcInspection.objects.create(
            pallet_barcode="PAL-TRIM-202611-002",
            part=sample_part,
            batch_quantity=1000,
            sample_size=80,
            defects_found=1,  # 1 defect violates c=0
            packaging_box_intact=True,
            esd_bag_sealed=True,
            desiccant_present=True,
            datamatrix_verified=True,
        )

        OqcDefectItem.objects.create(
            inspection=inspection,
            defect_type="SINK_MARK",
            severity="MAJOR",
            defect_count=1,
            notes="Sink mark on class-A surface",
        )

        released, coc_number, msg = evaluate_and_release_oqc(inspection, inspector_user)

        assert released is False
        assert coc_number == ""
        assert inspection.status == "REJECTED"

        event = OutboxEvent.objects.filter(
            event_type="qms.oqc_rejected",
            destination_system="WMS",
        ).first()
        assert event is not None
        assert event.payload["pallet_barcode"] == "PAL-TRIM-202611-002"
        assert event.payload["status"] == "QUARANTINE"

    def test_oqc_packaging_failure_rejects_lot(self, sample_part, inspector_user):
        inspection = OqcInspection.objects.create(
            pallet_barcode="PAL-TRIM-202611-003",
            part=sample_part,
            batch_quantity=1000,
            sample_size=80,
            defects_found=0,
            packaging_box_intact=True,
            esd_bag_sealed=False,  # ESD unsealed
            desiccant_present=True,
            datamatrix_verified=True,
        )

        released, coc_number, msg = evaluate_and_release_oqc(inspection, inspector_user)

        assert released is False
        assert inspection.status == "REJECTED"
        assert "Packaging checklist" in msg
