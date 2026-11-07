import json
import math
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponseBadRequest
from .models.spc import SpcControlChart
from .services import record_spc_subgroup


def spc_dashboard_view(request, chart_id=None):
    charts = SpcControlChart.objects.filter(is_active=True).order_by("characteristic_name")

    selected_chart = None
    if chart_id:
        selected_chart = get_object_or_404(SpcControlChart, id=chart_id)
    elif charts.exists():
        selected_chart = charts.first()

    subgroups = []
    nelson_violations_count = 0
    recent_violations = []
    chart_data_json = "{}"
    bell_curve_json = "[]"

    if selected_chart:
        subgroups = list(selected_chart.subgroups.order_by("subgroup_number"))

        # Calculate recent violations
        for s in subgroups:
            if s.nelson_rules_violated:
                nelson_violations_count += 1
                recent_violations.append({
                    "subgroup_number": s.subgroup_number,
                    "mean": float(s.mean),
                    "rules": s.nelson_rules_violated,
                    "recorded_at": s.created_at.strftime("%H:%M:%S") if s.created_at else "",
                })

        # Shewhart Chart Payload
        chart_payload = {
            "labels": [f"SG-{s.subgroup_number}" for s in subgroups],
            "means": [float(s.mean) for s in subgroups],
            "ranges": [float(s.range_val) for s in subgroups],
            "ucl": float(selected_chart.ucl) if selected_chart.ucl is not None else None,
            "lcl": float(selected_chart.lcl) if selected_chart.lcl is not None else None,
            "cl": float(selected_chart.center_line) if selected_chart.center_line is not None else None,
            "usl": float(selected_chart.usl),
            "lsl": float(selected_chart.lsl),
            "nominal": float(selected_chart.nominal),
            "violations": [
                {"x": i, "rules": s.nelson_rules_violated}
                for i, s in enumerate(subgroups)
                if s.nelson_rules_violated
            ],
        }
        chart_data_json = json.dumps(chart_payload)

        # Normal Bell Curve Calculation (Gaussian distribution)
        if selected_chart.center_line and float(selected_chart.cp or 0) > 0:
            mu = float(selected_chart.center_line)
            # Estimate sigma from Cp: Cp = (USL - LSL) / (6 * sigma) => sigma = (USL - LSL) / (6 * Cp)
            spec_w = float(selected_chart.usl) - float(selected_chart.lsl)
            cp_val = float(selected_chart.cp)
            sigma = (spec_w / (6.0 * cp_val)) if cp_val > 0 else 0.01

            curve_points = []
            steps = 40
            x_min = mu - 3.8 * sigma
            x_max = mu + 3.8 * sigma
            dx = (x_max - x_min) / steps

            for step in range(steps + 1):
                x_val = x_min + step * dx
                # Normal PDF formula: (1 / (sigma * sqrt(2*pi))) * exp(-0.5 * ((x - mu)/sigma)^2)
                pdf_val = (1.0 / (sigma * math.sqrt(2.0 * math.pi))) * math.exp(-0.5 * ((x_val - mu) / sigma) ** 2)
                curve_points.append({"x": round(x_val, 4), "y": round(pdf_val, 4)})

            bell_curve_json = json.dumps(curve_points)

    context = {
        "charts": charts,
        "selected_chart": selected_chart,
        "subgroups": subgroups[-15:] if subgroups else [],
        "total_subgroups": len(subgroups),
        "nelson_violations_count": nelson_violations_count,
        "recent_violations": recent_violations[-5:],
        "chart_data_json": chart_data_json,
        "bell_curve_json": bell_curve_json,
    }
    return render(request, "spc/index.html", context)


def spc_record_subgroup_view(request):
    """
    POST handler to ingest subgroup samples (e.g., from digital gauge terminal or manual entry).
    """
    if request.method != "POST":
        return HttpResponseBadRequest("Method not allowed. Use POST.")

    chart_id = request.POST.get("chart_id")
    raw_samples = request.POST.get("sample_values", "")

    if not chart_id or not raw_samples:
        messages.error(request, "Missing chart identifier or sample measurement values.")
        return redirect("spc:index")

    chart = get_object_or_404(SpcControlChart, id=chart_id)

    try:
        # Parse comma-separated or whitespace-separated numbers
        samples = [
            float(token.strip())
            for token in raw_samples.replace(",", " ").split()
            if token.strip()
        ]
    except ValueError:
        messages.error(request, "Invalid numeric input in subgroup samples.")
        return redirect("spc:chart_detail", chart_id=chart.id)

    if len(samples) != chart.subgroup_size:
        messages.error(
            request,
            f"Expected exactly {chart.subgroup_size} sample measurements for this chart (received {len(samples)}).",
        )
        return redirect("spc:chart_detail", chart_id=chart.id)

    subgroup = record_spc_subgroup(chart.id, samples)

    if subgroup.nelson_rules_violated:
        rule_nums = ", ".join(f"Rule #{r}" for r in subgroup.nelson_rules_violated)
        messages.warning(
            request,
            f"Subgroup #{subgroup.subgroup_number} recorded. ANOMALY DETECTED: {rule_nums} violated!",
        )
    else:
        messages.success(
            request,
            (
                f"Subgroup #{subgroup.subgroup_number} recorded successfully. "
                f"Mean: {subgroup.mean}, Range: {subgroup.range_val}."
            ),
        )

    return redirect("spc:chart_detail", chart_id=chart.id)
