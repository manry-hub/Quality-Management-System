import math
import uuid
from decimal import Decimal
from typing import Tuple, List
from django.db import transaction
from django.utils import timezone
from .models.metrology import (
    Gauge,
    GaugeCalibration,
    GaugeStatusChoices,
    MsaStudy,
    MsaAcceptanceChoices,
)


def check_gauge_lockout(device_id_or_instance) -> Tuple[bool, str]:
    """
    Checks if a gauge is locked out from floor quality measurements
    due to expired calibration or out-of-service status.
    Automatically marks overdue gauges.
    Returns (is_locked_out, reason).
    """
    if isinstance(device_id_or_instance, Gauge):
        gauge = device_id_or_instance
    else:
        try:
            gauge = Gauge.objects.get(device_id=device_id_or_instance)
        except Gauge.DoesNotExist:
            return True, f"Gauge '{device_id_or_instance}' does not exist in Metrology registry."

    today = timezone.now().date()

    if gauge.status == GaugeStatusChoices.OUT_OF_SERVICE:
        return True, f"Measurement Lockout: Gauge {gauge.device_id} is OUT OF SERVICE."

    if gauge.next_calibration_due < today:
        if gauge.status != GaugeStatusChoices.OVERDUE:
            gauge.status = GaugeStatusChoices.OVERDUE
            gauge.save(update_fields=["status", "updated_at"])
        return (
            True,
            f"Measurement Lockout: Calibration expired on {gauge.next_calibration_due}. Recalibration required.",
        )

    if gauge.status == GaugeStatusChoices.OVERDUE:
        return True, f"Measurement Lockout: Gauge {gauge.device_id} is marked OVERDUE."

    return False, "Gauge is active with valid calibration certificate."


@transaction.atomic
def record_calibration(
    gauge: Gauge,
    certificate_number: str,
    calibration_date,
    calibrated_by: str,
    next_due_date,
    as_found_condition: str = "IN_TOLERANCE",
    as_left_condition: str = "IN_TOLERANCE",
    uncertainty_budget_mm: float = 0.0020,
    notes: str = "",
) -> GaugeCalibration:
    """
    Registers a certified calibration event and clears any active inspection lockouts.
    """
    cal_record = GaugeCalibration.objects.create(
        gauge=gauge,
        certificate_number=certificate_number,
        calibration_date=calibration_date,
        calibrated_by=calibrated_by,
        as_found_condition=as_found_condition,
        as_left_condition=as_left_condition,
        uncertainty_budget_mm=Decimal(str(uncertainty_budget_mm)),
        notes=notes,
    )

    gauge.last_calibration_date = calibration_date
    gauge.next_calibration_due = next_due_date
    gauge.status = GaugeStatusChoices.ACTIVE
    gauge.save(update_fields=["last_calibration_date", "next_calibration_due", "status", "updated_at"])

    return cal_record


@transaction.atomic
def compute_anova_gauge_rr(study_id: uuid.UUID) -> MsaStudy:
    """
    Executes AIAG MSA 4th Edition ANOVA Gauge Repeatability & Reproducibility (Gauge R&R).
    raw_data is a 3D matrix of shape [part_count][operator_count][trial_count].
    Calculates EV, AV, GRR, PV, TV, %GRR, and Number of Distinct Categories (ndc).
    """
    study = MsaStudy.objects.select_for_update().get(id=study_id)
    raw_data: List[List[List[float]]] = study.raw_data

    p = len(raw_data)  # Parts
    if p == 0:
        return study
    o = len(raw_data[0])  # Operators
    if o == 0:
        return study
    t = len(raw_data[0][0])  # Trials
    if t == 0:
        return study

    n_total = p * o * t

    # Flatten and calculate total sum
    flat_values = []
    part_totals = [0.0] * p
    operator_totals = [0.0] * o
    cell_totals = [[0.0] * o for _ in range(p)]

    for i in range(p):
        for j in range(o):
            for k in range(t):
                val = float(raw_data[i][j][k])
                flat_values.append(val)
                part_totals[i] += val
                operator_totals[j] += val
                cell_totals[i][j] += val

    grand_total = sum(flat_values)
    cf = (grand_total ** 2) / n_total

    ss_total = sum(x ** 2 for x in flat_values) - cf
    ss_parts = sum(pt ** 2 for pt in part_totals) / (o * t) - cf
    ss_operators = sum(ot ** 2 for ot in operator_totals) / (p * t) - cf

    ss_cells = sum(sum(cell ** 2 for cell in row) for row in cell_totals) / t - cf
    ss_interaction = max(0.0, ss_cells - ss_parts - ss_operators)
    ss_repeatability = max(0.0, ss_total - ss_cells)

    df_parts = p - 1
    df_operators = o - 1
    df_interaction = (p - 1) * (o - 1)
    df_repeatability = p * o * (t - 1)

    ms_parts = ss_parts / df_parts if df_parts > 0 else 0.0
    ms_operators = ss_operators / df_operators if df_operators > 0 else 0.0
    ms_interaction = ss_interaction / df_interaction if df_interaction > 0 else 0.0
    ms_repeatability = ss_repeatability / df_repeatability if df_repeatability > 0 else 0.0

    # AIAG ANOVA Variance Component Estimation
    # Pool interaction if interaction is not significant or ms_interaction <= ms_repeatability
    if ms_interaction <= ms_repeatability or df_interaction == 0:
        ss_pooled = ss_interaction + ss_repeatability
        df_pooled = df_interaction + df_repeatability
        ms_error = ss_pooled / df_pooled if df_pooled > 0 else ms_repeatability

        var_repeatability = ms_error
        var_operator = max(0.0, (ms_operators - ms_error) / (p * t))
        var_part = max(0.0, (ms_parts - ms_error) / (o * t))
        var_reproducibility = var_operator
    else:
        var_repeatability = ms_repeatability
        var_interaction = max(0.0, (ms_interaction - ms_repeatability) / t)
        var_operator = max(0.0, (ms_operators - ms_interaction) / (p * t))
        var_reproducibility = var_operator + var_interaction
        var_part = max(0.0, (ms_parts - ms_interaction) / (o * t))

    ev = math.sqrt(var_repeatability)
    av = math.sqrt(var_reproducibility)
    grr = math.sqrt(var_repeatability + var_reproducibility)
    pv = math.sqrt(var_part)
    tv = math.sqrt(grr ** 2 + pv ** 2)

    # %GRR = 100 * (GRR / TV)
    grr_pct = (100.0 * grr / tv) if tv > 0 else 0.0

    # ndc = 1.41 * (PV / GRR)
    ndc_val = (1.41 * (pv / grr)) if grr > 0 else 0.0

    # AIAG Acceptance Criteria
    if grr_pct <= 10.0 and ndc_val >= 5.0:
        status = MsaAcceptanceChoices.ACCEPTABLE
    elif grr_pct <= 30.0 and ndc_val >= 4.0:
        status = MsaAcceptanceChoices.MARGINAL
    else:
        status = MsaAcceptanceChoices.UNACCEPTABLE

    study.repeatability_ev = Decimal(f"{ev:.5f}")
    study.reproducibility_av = Decimal(f"{av:.5f}")
    study.grr = Decimal(f"{grr:.5f}")
    study.part_variation_pv = Decimal(f"{pv:.5f}")
    study.total_variation_tv = Decimal(f"{tv:.5f}")
    study.grr_percent = Decimal(f"{grr_pct:.2f}")
    study.ndc = Decimal(f"{ndc_val:.1f}")
    study.acceptance_status = status
    study.save()

    return study
