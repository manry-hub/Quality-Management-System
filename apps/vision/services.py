from decimal import Decimal
from typing import List, Dict, Any, Optional
from django.db import transaction
from django.contrib.auth import get_user_model
from apps.master_data.models import Part
from apps.ncr.models.ncr import (
    SourceDomain,
    SeverityLevel,
    TargetType,
)
from apps.ncr.services import declare_quality_hold
from .models.vision import (
    VisionInspectionStation,
    VisionDefectInspection,
    DefectTypeChoices,
    DefectSeverityChoices,
    VisionActionChoices,
)

User = get_user_model()


@transaction.atomic
def classify_molding_defect(
    station: VisionInspectionStation,
    part: Part,
    shot_number: int,
    cavity_number: int = 1,
    simulated_detections: Optional[List[Dict[str, Any]]] = None,
    image_path: str = "",
    user=None,
) -> VisionDefectInspection:
    """
    Ingests vision camera detection telemetry, evaluates defect severity,
    and automatically triggers quarantine holds for critical defects.
    """
    if simulated_detections is None:
        simulated_detections = []

    # Filter detections meeting or exceeding station confidence threshold
    threshold = float(station.confidence_threshold)
    valid_detections = [
        d for d in simulated_detections
        if float(d.get("confidence", 0.0)) >= threshold
    ]

    severity_order = {
        DefectSeverityChoices.CRITICAL: 4,
        DefectSeverityChoices.MAJOR: 3,
        DefectSeverityChoices.MINOR: 2,
        DefectSeverityChoices.ACCEPTABLE: 1,
    }

    if valid_detections:
        # Sort by severity descending then confidence descending
        sorted_detections = sorted(
            valid_detections,
            key=lambda d: (severity_order.get(d.get("severity", "ACCEPTABLE"), 1), float(d.get("confidence", 0))),
            reverse=True,
        )
        top = sorted_detections[0]
        primary_defect = top.get("label", DefectTypeChoices.NO_DEFECT)
        severity = top.get("severity", DefectSeverityChoices.ACCEPTABLE)
        confidence = float(top.get("confidence", 0.95))
    else:
        primary_defect = DefectTypeChoices.NO_DEFECT
        severity = DefectSeverityChoices.ACCEPTABLE
        confidence = 0.9850

    # Determine automated action
    ncr_record = None
    if severity == DefectSeverityChoices.CRITICAL:
        action = VisionActionChoices.NCR_HOLD_TRIGGERED
        # Trigger formal automated quality hold
        if user is None:
            user = User.objects.filter(is_staff=True).first()

        ncr_record = declare_quality_hold(
            source_domain=SourceDomain.IPQC,
            severity=SeverityLevel.CRITICAL,
            target_type=TargetType.IN_PROCESS_RUN,
            target_identifier=f"{station.station_code}-SHOT-{shot_number}",
            defect_description=(
                f"AI Vision Inspection Station {station.station_code}: {primary_defect} detected with "
                f"{confidence * 100:.1f}% confidence on cavity {cavity_number}."
            ),
            containment_actions=(
                "Automated robot divert gate engaged; cavity marked for quarantine inspection."
            ),
            user=user,
        )
    elif severity in (DefectSeverityChoices.MAJOR, DefectSeverityChoices.MINOR):
        action = VisionActionChoices.REJECT_DIVERTED
    else:
        action = VisionActionChoices.CLEARED

    inspection = VisionDefectInspection.objects.create(
        station=station,
        part=part,
        shot_number=shot_number,
        cavity_number=cavity_number,
        primary_defect_type=primary_defect,
        confidence_score=Decimal(f"{confidence:.4f}"),
        severity=severity,
        bounding_boxes=simulated_detections,
        image_path=image_path,
        auto_action_taken=action,
        ncr=ncr_record,
    )

    return inspection
