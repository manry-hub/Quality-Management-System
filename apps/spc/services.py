import math
from decimal import Decimal
from typing import List, Dict, Any
from django.db import transaction
from .models import SpcControlChart, SpcSubgroup

# AIAG SPC Standard Unbiasing Constants for n=2 to n=10
# (Sample size n -> (A2, D3, D4, d2, c4))
SPC_CONSTANTS = {
    2: (1.880, 0.000, 3.267, 1.128, 0.7979),
    3: (1.023, 0.000, 2.574, 1.693, 0.8862),
    4: (0.729, 0.000, 2.282, 2.059, 0.9213),
    5: (0.577, 0.000, 2.114, 2.326, 0.9400),
    6: (0.483, 0.000, 2.004, 2.534, 0.9515),
    7: (0.419, 0.076, 1.924, 2.704, 0.9594),
    8: (0.373, 0.136, 1.864, 2.847, 0.9650),
    9: (0.337, 0.184, 1.816, 2.970, 0.9693),
    10: (0.308, 0.223, 1.777, 3.078, 0.9727),
}


def calculate_subgroup_metrics(sample_values: List[float]) -> Dict[str, float]:
    """
    Computes mean, range, and standard deviation for a single subgroup.
    """
    n = len(sample_values)
    if n == 0:
        return {"mean": 0.0, "range": 0.0, "std_dev": 0.0}

    mean_val = sum(sample_values) / n
    range_val = max(sample_values) - min(sample_values)
    if n > 1:
        variance = sum((x - mean_val) ** 2 for x in sample_values) / (n - 1)
        std_dev = math.sqrt(variance)
    else:
        std_dev = 0.0

    return {
        "mean": round(mean_val, 4),
        "range": round(range_val, 4),
        "std_dev": round(std_dev, 4),
    }


def evaluate_nelson_rules(
    means_series: List[float],
    center_line: float,
    sigma: float,
) -> List[int]:
    """
    Automated evaluation of Nelson Rules 1 through 8 on the latest point in a subgroup means series.
    Each zone represents 1-sigma intervals:
      - Zone C: [CL - 1sigma, CL + 1sigma]
      - Zone B: [CL - 2sigma, CL - 1sigma) and (CL + 1sigma, CL + 2sigma]
      - Zone A: [CL - 3sigma, CL - 2sigma) and (CL + 2sigma, CL + 3sigma]
      - Beyond: > 3sigma
    """
    if not means_series or sigma <= 0:
        return []

    rules_violated = []
    latest = means_series[-1]
    n_points = len(means_series)

    # Rule 1: One point beyond Zone A (> 3 sigma from center line)
    if abs(latest - center_line) > 3.0 * sigma:
        rules_violated.append(1)

    # Rule 2: Nine consecutive points on one side of center line
    if n_points >= 9:
        last_9 = means_series[-9:]
        if all(x > center_line for x in last_9) or all(x < center_line for x in last_9):
            rules_violated.append(2)

    # Rule 3: Six consecutive points strictly increasing or strictly decreasing
    if n_points >= 6:
        last_6 = means_series[-6:]
        increasing = all(last_6[i] < last_6[i + 1] for i in range(5))
        decreasing = all(last_6[i] > last_6[i + 1] for i in range(5))
        if increasing or decreasing:
            rules_violated.append(3)

    # Rule 4: Fourteen consecutive points alternating up and down
    if n_points >= 14:
        last_14 = means_series[-14:]
        diffs = [last_14[i + 1] - last_14[i] for i in range(13)]
        alternating = all((diffs[i] * diffs[i + 1]) < 0 for i in range(12))
        if alternating:
            rules_violated.append(4)

    # Rule 5: Two out of three consecutive points beyond 2 sigma on the same side
    if n_points >= 3:
        last_3 = means_series[-3:]
        upper_2sigma = [x for x in last_3 if x > center_line + 2.0 * sigma]
        lower_2sigma = [x for x in last_3 if x < center_line - 2.0 * sigma]
        if len(upper_2sigma) >= 2 or len(lower_2sigma) >= 2:
            rules_violated.append(5)

    # Rule 6: Four out of five consecutive points beyond 1 sigma on the same side
    if n_points >= 5:
        last_5 = means_series[-5:]
        upper_1sigma = [x for x in last_5 if x > center_line + 1.0 * sigma]
        lower_1sigma = [x for x in last_5 if x < center_line - 1.0 * sigma]
        if len(upper_1sigma) >= 4 or len(lower_1sigma) >= 4:
            rules_violated.append(6)

    # Rule 7: Fifteen consecutive points within 1 sigma of center line (stratification)
    if n_points >= 15:
        last_15 = means_series[-15:]
        if all(abs(x - center_line) <= 1.0 * sigma for x in last_15):
            rules_violated.append(7)

    # Rule 8: Eight consecutive points beyond 1 sigma on either side with none in Zone C
    if n_points >= 8:
        last_8 = means_series[-8:]
        if all(abs(x - center_line) > 1.0 * sigma for x in last_8):
            rules_violated.append(8)

    return sorted(rules_violated)


@transaction.atomic
def calculate_control_limits_and_capability(chart: SpcControlChart) -> Dict[str, Any]:
    """
    Computes X-bar control limits and ISO 21747 Process Capability indices (Cp, Cpk, Pp, Ppk).
    """
    subgroups = list(chart.subgroups.order_by("subgroup_number"))
    if not subgroups:
        return {}

    n = chart.subgroup_size
    consts = SPC_CONSTANTS.get(n, SPC_CONSTANTS[5])
    a2, d3, d4, d2, c4 = consts

    means = [float(s.mean) for s in subgroups]
    ranges = [float(s.range_val) for s in subgroups]

    grand_mean = sum(means) / len(means)
    avg_range = sum(ranges) / len(ranges) if ranges else 0.0

    # Within-subgroup standard deviation (R-bar / d2)
    sigma_within = avg_range / d2 if d2 > 0 else 0.001

    # Control Limits
    ucl = grand_mean + a2 * avg_range
    lcl = max(0.0, grand_mean - a2 * avg_range)

    # Overall standard deviation across all individual pooled samples
    all_samples = []
    for s in subgroups:
        all_samples.extend([float(v) for v in s.sample_values])

    if len(all_samples) > 1:
        overall_mean = sum(all_samples) / len(all_samples)
        overall_var = sum((x - overall_mean) ** 2 for x in all_samples) / (len(all_samples) - 1)
        sigma_overall = math.sqrt(overall_var)
    else:
        sigma_overall = sigma_within

    usl = float(chart.usl)
    lsl = float(chart.lsl)
    spec_width = usl - lsl

    # Capability (Cp, Cpk)
    if sigma_within > 0:
        cp = spec_width / (6.0 * sigma_within)
        cpk_upper = (usl - grand_mean) / (3.0 * sigma_within)
        cpk_lower = (grand_mean - lsl) / (3.0 * sigma_within)
        cpk = min(cpk_upper, cpk_lower)
    else:
        cp, cpk = 0.0, 0.0

    # Performance (Pp, Ppk)
    if sigma_overall > 0:
        pp = spec_width / (6.0 * sigma_overall)
        ppk_upper = (usl - grand_mean) / (3.0 * sigma_overall)
        ppk_lower = (grand_mean - lsl) / (3.0 * sigma_overall)
        ppk = min(ppk_upper, ppk_lower)
    else:
        pp, ppk = 0.0, 0.0

    chart.center_line = Decimal(f"{grand_mean:.4f}")
    chart.ucl = Decimal(f"{ucl:.4f}")
    chart.lcl = Decimal(f"{lcl:.4f}")
    chart.cp = Decimal(f"{cp:.3f}")
    chart.cpk = Decimal(f"{cpk:.3f}")
    chart.pp = Decimal(f"{pp:.3f}")
    chart.ppk = Decimal(f"{ppk:.3f}")
    chart.save()

    return {
        "center_line": grand_mean,
        "ucl": ucl,
        "lcl": lcl,
        "sigma_within": sigma_within,
        "sigma_overall": sigma_overall,
        "cp": cp,
        "cpk": cpk,
        "pp": pp,
        "ppk": ppk,
    }


@transaction.atomic
def record_spc_subgroup(chart_id, sample_values: List[float]) -> SpcSubgroup:
    """
    Ingests a new subgroup, executes Nelson Rules evaluation, and updates capability indices.
    """
    chart = SpcControlChart.objects.select_for_update().get(id=chart_id)
    metrics = calculate_subgroup_metrics(sample_values)

    existing_subgroups = list(chart.subgroups.order_by("subgroup_number"))
    next_num = (existing_subgroups[-1].subgroup_number + 1) if existing_subgroups else 1

    # Historical means including the new point
    means_history = [float(s.mean) for s in existing_subgroups] + [metrics["mean"]]

    # Sigma for Nelson rules (either from existing control limits or from subgroup std_dev)
    consts = SPC_CONSTANTS.get(chart.subgroup_size, SPC_CONSTANTS[5])
    d2 = consts[3]
    if chart.center_line and chart.ucl and chart.lcl:
        cl = float(chart.center_line)
        sigma_est = (float(chart.ucl) - cl) / 3.0
    else:
        cl = float(chart.nominal)
        ranges = [float(s.range_val) for s in existing_subgroups] + [metrics["range"]]
        avg_r = sum(ranges) / len(ranges)
        sigma_est = (avg_r / d2) if d2 > 0 else 0.01

    rules_violated = evaluate_nelson_rules(
        means_series=means_history,
        center_line=cl,
        sigma=sigma_est,
    )

    subgroup = SpcSubgroup.objects.create(
        chart=chart,
        subgroup_number=next_num,
        sample_values=[round(float(v), 4) for v in sample_values],
        sample_size=len(sample_values),
        mean=Decimal(str(metrics["mean"])),
        range_val=Decimal(str(metrics["range"])),
        std_dev=Decimal(str(metrics["std_dev"])),
        nelson_rules_violated=rules_violated,
    )

    # Recalculate control limits and capability after updating subgroups
    calculate_control_limits_and_capability(chart)

    return subgroup
