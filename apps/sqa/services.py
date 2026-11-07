from decimal import Decimal
from typing import Tuple, List, Dict, Any
from django.db import transaction
from django.utils import timezone
from apps.master_data.models import ResinMaterial
from apps.core.models.audit import AuditTrailEvent
from .models.sqa import (
    Supplier,
    CertificateOfAnalysis,
    SupplierScorecard,
    CoaStatusChoices,
    ScorecardGradeChoices,
)


def validate_coa_data(
    material: ResinMaterial,
    parameters: Dict[str, Any],
) -> Tuple[bool, float, List[str]]:
    """
    Validates supplier Certificate of Analysis (CoA) parameters against engineering
    material master specifications (moisture % and MFI limits).
    Returns (is_compliant, compliance_score, deviations).
    """
    deviations = []
    score = 100.0

    # 1. Moisture % verification
    if "moisture_pct" in parameters:
        moisture = Decimal(str(parameters["moisture_pct"]))
        if moisture > material.target_moisture_max_pct:
            deviations.append(
                f"Moisture content {moisture}% exceeds material max specification "
                f"{material.target_moisture_max_pct}%"
            )
            score -= 40.0

    # 2. Melt Flow Index (MFI) verification
    if "mfi_g_10min" in parameters:
        mfi = Decimal(str(parameters["mfi_g_10min"]))
        nominal = material.target_mfi_nominal
        tol = material.target_mfi_tolerance
        min_allowed = nominal - tol
        max_allowed = nominal + tol

        if mfi < min_allowed or mfi > max_allowed:
            deviations.append(
                f"MFI {mfi} g/10min is out of specification range [{min_allowed} - {max_allowed}] g/10min"
            )
            score -= 40.0

    # 3. Density check (optional)
    if "density_g_cm3" in parameters:
        density = Decimal(str(parameters["density_g_cm3"]))
        if density <= Decimal("0.5") or density >= Decimal("2.5"):
            deviations.append(f"Unusual polymer density {density} g/cm3")
            score -= 20.0

    score = max(0.0, score)
    is_compliant = len(deviations) == 0

    return is_compliant, round(score, 2), deviations


@transaction.atomic
def ingest_supplier_coa(
    coa_number: str,
    supplier: Supplier,
    material: ResinMaterial,
    lot_number: str,
    manufacture_date,
    parameters: Dict[str, Any],
    user=None,
    expiration_date=None,
) -> CertificateOfAnalysis:
    """
    Ingests, validates, and archives a supplier Certificate of Analysis.
    """
    is_compliant, score, deviations = validate_coa_data(material, parameters)
    status = CoaStatusChoices.APPROVED if is_compliant else CoaStatusChoices.REJECTED

    coa = CertificateOfAnalysis.objects.create(
        coa_number=coa_number,
        supplier=supplier,
        material=material,
        lot_number=lot_number,
        manufacture_date=manufacture_date,
        expiration_date=expiration_date,
        parameters=parameters,
        compliance_score=Decimal(str(score)),
        status=status,
        verified_by=user,
        verified_at=timezone.now(),
        deviation_notes="; ".join(deviations),
    )

    if not is_compliant and user:
        AuditTrailEvent.objects.create(
            action_type="COA_REJECTED",
            entity_type="CertificateOfAnalysis",
            entity_id=coa.id,
            badge_number=getattr(user, "badge_number", "QA-AUTO"),
            signature_manifestation=(
                f"CoA {coa_number} for Lot {lot_number} rejected due to spec deviation: {coa.deviation_notes}"
            ),
            payload_snapshot={"deviations": deviations, "parameters": parameters},
        )

    return coa


@transaction.atomic
def compute_supplier_scorecard(
    supplier: Supplier,
    period_label: str,
    on_time_delivery_pct: float = 98.0,
) -> SupplierScorecard:
    """
    Computes periodic supplier performance scorecard, lot acceptance rate, PPM defect rate,
    and assigns quality performance grade (A/B/C/D).
    """
    coas = supplier.coas.all()
    total_lots = coas.count()
    accepted_lots = coas.filter(status=CoaStatusChoices.APPROVED).count()
    rejected_lots = coas.filter(status=CoaStatusChoices.REJECTED).count()

    coa_compliance_pct = (accepted_lots / total_lots * 100.0) if total_lots > 0 else 100.0

    # Parts Per Million (PPM) defect rate based on received lots
    ppm_rate = (rejected_lots / total_lots * 1_000_000.0) if total_lots > 0 else 0.0

    # Composite evaluation score (0 - 100)
    # 50% CoA compliance, 30% on-time delivery, 20% PPM performance
    ppm_penalty = min(100.0, ppm_rate / 1000.0)
    composite_score = (
        0.50 * coa_compliance_pct +
        0.30 * on_time_delivery_pct +
        0.20 * (100.0 - ppm_penalty)
    )

    if composite_score >= 95.0:
        grade = ScorecardGradeChoices.GRADE_A
    elif composite_score >= 85.0:
        grade = ScorecardGradeChoices.GRADE_B
    elif composite_score >= 70.0:
        grade = ScorecardGradeChoices.GRADE_C
    else:
        grade = ScorecardGradeChoices.GRADE_D

    scorecard, _ = SupplierScorecard.objects.update_or_create(
        supplier=supplier,
        period_label=period_label,
        defaults={
            "total_lots_supplied": total_lots,
            "accepted_lots": accepted_lots,
            "rejected_lots": rejected_lots,
            "ppm_defect_rate": Decimal(f"{ppm_rate:.2f}"),
            "on_time_delivery_pct": Decimal(f"{on_time_delivery_pct:.2f}"),
            "coa_compliance_pct": Decimal(f"{coa_compliance_pct:.2f}"),
            "grade": grade,
        },
    )

    return scorecard
