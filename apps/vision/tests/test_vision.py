from decimal import Decimal
import pytest
from django.urls import reverse
from apps.master_data.models import Part, ResinMaterial, PolymerTypeChoices
from apps.vision.models.vision import (
    VisionInspectionStation,
    VisionDefectInspection,
    DefectTypeChoices,
    DefectSeverityChoices,
    VisionActionChoices,
)
from apps.vision.services import classify_molding_defect


@pytest.fixture
def vision_part(db):
    material = ResinMaterial.objects.create(
        material_code="MAT-VIS-PP",
        material_name="Vision Polypropylene",
        polymer_type=PolymerTypeChoices.PP,
        supplier_code="SUP-VIS",
        target_moisture_max_pct=Decimal("0.02"),
        target_mfi_nominal=Decimal("12.0"),
        target_mfi_tolerance=Decimal("1.5"),
    )
    return Part.objects.create(
        part_number="PRD-VIS-001",
        part_name="Vision Test Fascia",
        drawing_number="DWG-VIS-1",
        drawing_revision="A",
        material_code=material.material_code,
    )


@pytest.fixture
def vision_station(db):
    return VisionInspectionStation.objects.create(
        station_code="CAM-TEST-01",
        name="Basler ace 2 Test Station",
        line_cell="CELL-TEST-01",
        camera_model="Basler ace 2 Test",
        resolution="1920x1080",
        confidence_threshold=Decimal("0.85"),
        is_online=True,
    )


@pytest.mark.django_db
def test_classify_molding_defect_clean_shot(vision_station, vision_part):
    inspection = classify_molding_defect(
        station=vision_station,
        part=vision_part,
        shot_number=101,
        cavity_number=1,
        simulated_detections=[],
    )
    assert inspection.id is not None
    assert inspection.primary_defect_type == DefectTypeChoices.NO_DEFECT
    assert inspection.severity == DefectSeverityChoices.ACCEPTABLE
    assert inspection.auto_action_taken == VisionActionChoices.CLEARED
    assert inspection.ncr is None


@pytest.mark.django_db
def test_classify_molding_defect_divert_minor(vision_station, vision_part):
    detections = [
        {
            "label": DefectTypeChoices.SINK_MARK,
            "confidence": 0.90,
            "severity": DefectSeverityChoices.MINOR,
            "bbox": [100, 100, 50, 30],
        }
    ]
    inspection = classify_molding_defect(
        station=vision_station,
        part=vision_part,
        shot_number=102,
        cavity_number=1,
        simulated_detections=detections,
    )
    assert inspection.primary_defect_type == DefectTypeChoices.SINK_MARK
    assert inspection.severity == DefectSeverityChoices.MINOR
    assert inspection.auto_action_taken == VisionActionChoices.REJECT_DIVERTED
    assert inspection.ncr is None


@pytest.mark.django_db
def test_classify_molding_defect_critical_triggers_ncr_hold(vision_station, vision_part):
    detections = [
        {
            "label": DefectTypeChoices.FLASH,
            "confidence": 0.96,
            "severity": DefectSeverityChoices.CRITICAL,
            "bbox": [150, 80, 70, 25],
        }
    ]
    inspection = classify_molding_defect(
        station=vision_station,
        part=vision_part,
        shot_number=103,
        cavity_number=2,
        simulated_detections=detections,
    )
    assert inspection.primary_defect_type == DefectTypeChoices.FLASH
    assert inspection.severity == DefectSeverityChoices.CRITICAL
    assert inspection.auto_action_taken == VisionActionChoices.NCR_HOLD_TRIGGERED
    assert inspection.ncr is not None
    assert inspection.ncr.hold_declared is True
    assert "Vision Inspection Station CAM-TEST-01" in inspection.ncr.defect_description


@pytest.mark.django_db
def test_classify_molding_defect_below_threshold(vision_station, vision_part):
    # Station threshold is 0.85; detection confidence is 0.75
    detections = [
        {
            "label": DefectTypeChoices.BURN_MARK,
            "confidence": 0.75,
            "severity": DefectSeverityChoices.MAJOR,
            "bbox": [50, 50, 20, 20],
        }
    ]
    inspection = classify_molding_defect(
        station=vision_station,
        part=vision_part,
        shot_number=104,
        cavity_number=1,
        simulated_detections=detections,
    )
    # Filtered out due to confidence < 0.85
    assert inspection.primary_defect_type == DefectTypeChoices.NO_DEFECT
    assert inspection.auto_action_taken == VisionActionChoices.CLEARED


@pytest.mark.django_db
def test_vision_views(client, vision_station, vision_part):
    # 1. Vision Console
    res = client.get(reverse("vision:index"))
    assert res.status_code == 200
    assert "AI Vision Inspection" in res.content.decode()

    # 2. Station Detail
    res = client.get(reverse("vision:station_detail", kwargs={"station_id": vision_station.id}))
    assert res.status_code == 200
    assert vision_station.station_code in res.content.decode()

    # 3. Simulate Shot POST
    sim_data = {
        "station_id": vision_station.id,
        "part_id": vision_part.id,
        "shot_number": "205",
        "cavity_number": "1",
        "defect_type": DefectTypeChoices.SHORT_SHOT,
        "severity": DefectSeverityChoices.MAJOR,
        "confidence_score": "0.93",
    }
    res = client.post(reverse("vision:simulate_shot"), sim_data)
    assert res.status_code == 302
    assert VisionDefectInspection.objects.filter(
        shot_number=205, primary_defect_type=DefectTypeChoices.SHORT_SHOT
    ).exists()
