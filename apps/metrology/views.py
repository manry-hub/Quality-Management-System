from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponseBadRequest
from django.utils import timezone
from apps.master_data.models import Part
from .models.metrology import (
    Gauge,
    GaugeStatusChoices,
    GaugeTypeChoices,
    MsaStudy,
)
from .services import (
    check_gauge_lockout,
    record_calibration,
    compute_anova_gauge_rr,
)


def metrology_index_view(request):
    # Dynamic scan for overdue calibration lockout
    all_gauges = list(Gauge.objects.all())
    for g in all_gauges:
        check_gauge_lockout(g)

    status_filter = request.GET.get("status")
    type_filter = request.GET.get("type")

    queryset = Gauge.objects.all().order_by("device_id")
    if status_filter:
        queryset = queryset.filter(status=status_filter)
    if type_filter:
        queryset = queryset.filter(gauge_type=type_filter)

    gauges = list(queryset)

    # Metrics
    total_gauges = len(all_gauges)
    active_gauges = sum(1 for g in all_gauges if g.status == GaugeStatusChoices.ACTIVE)
    locked_out_gauges = sum(1 for g in all_gauges if g.status == GaugeStatusChoices.OVERDUE)
    out_of_service = sum(1 for g in all_gauges if g.status == GaugeStatusChoices.OUT_OF_SERVICE)

    today = timezone.now().date()
    expiring_soon = sum(
        1 for g in all_gauges
        if g.status == GaugeStatusChoices.ACTIVE and 0 <= (g.next_calibration_due - today).days <= 30
    )

    msa_studies = MsaStudy.objects.select_related("gauge", "part").order_by("-created_at")[:10]
    parts = Part.objects.all().order_by("part_number")

    context = {
        "gauges": gauges,
        "total_gauges": total_gauges,
        "active_gauges": active_gauges,
        "locked_out_gauges": locked_out_gauges,
        "out_of_service": out_of_service,
        "expiring_soon": expiring_soon,
        "msa_studies": msa_studies,
        "parts": parts,
        "status_filter": status_filter,
        "type_filter": type_filter,
        "gauge_types": GaugeTypeChoices.choices,
        "status_choices": GaugeStatusChoices.choices,
    }
    return render(request, "metrology/index.html", context)


def record_calibration_view(request, gauge_id):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required.")

    gauge = get_object_or_404(Gauge, id=gauge_id)
    cert_number = request.POST.get("certificate_number", "").strip()
    calibrated_by = request.POST.get("calibrated_by", "").strip()
    cal_date_str = request.POST.get("calibration_date")
    next_due_str = request.POST.get("next_calibration_due")
    as_found = request.POST.get("as_found_condition", "IN_TOLERANCE")
    as_left = request.POST.get("as_left_condition", "IN_TOLERANCE")
    uncertainty_str = request.POST.get("uncertainty_budget_mm", "0.0020")
    notes = request.POST.get("notes", "").strip()

    if not cert_number or not calibrated_by or not cal_date_str or not next_due_str:
        messages.error(request, "Please provide Certificate Number, Calibrated By, and valid dates.")
        return redirect("metrology:index")

    try:
        cal_date = timezone.datetime.strptime(cal_date_str, "%Y-%m-%d").date()
        next_due = timezone.datetime.strptime(next_due_str, "%Y-%m-%d").date()
        uncertainty = float(uncertainty_str)
    except (ValueError, TypeError):
        messages.error(request, "Invalid dates or numeric format.")
        return redirect("metrology:index")

    cal = record_calibration(
        gauge=gauge,
        certificate_number=cert_number,
        calibration_date=cal_date,
        calibrated_by=calibrated_by,
        next_due_date=next_due,
        as_found_condition=as_found,
        as_left_condition=as_left,
        uncertainty_budget_mm=uncertainty,
        notes=notes,
    )

    messages.success(
        request,
        f"Calibration {cal.certificate_number} recorded. Lockout CLEARED for {gauge.device_id}. Next due: {next_due}.",
    )
    return redirect("metrology:index")


def msa_study_detail_view(request, study_id):
    study = get_object_or_404(MsaStudy.objects.select_related("gauge", "part"), id=study_id)

    # Compute if not yet calculated
    if study.grr_percent is None and study.raw_data:
        compute_anova_gauge_rr(study.id)
        study.refresh_from_db()

    # Flatten raw matrix for readable inspection in template
    raw_matrix = []
    if study.raw_data:
        for p_idx, part_trials in enumerate(study.raw_data):
            part_num = p_idx + 1
            for o_idx, op_trials in enumerate(part_trials):
                op_num = f"Op {chr(65 + o_idx)}"
                raw_matrix.append({
                    "part": part_num,
                    "operator": op_num,
                    "trials": op_trials,
                    "mean": round(sum(op_trials) / len(op_trials), 4) if op_trials else 0.0,
                    "range": round(max(op_trials) - min(op_trials), 4) if op_trials else 0.0,
                })

    context = {
        "study": study,
        "raw_matrix": raw_matrix,
    }
    return render(request, "metrology/msa_detail.html", context)


def run_msa_study_view(request, study_id):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required.")

    study = get_object_or_404(MsaStudy, id=study_id)
    compute_anova_gauge_rr(study.id)
    messages.success(request, f"AIAG ANOVA Gauge R&R calculated for study {study.study_number}.")
    return redirect("metrology:msa_detail", study_id=study.id)


def msa_study_create_view(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required.")

    gauge_id = request.POST.get("gauge_id")
    part_id = request.POST.get("part_id")
    characteristic = request.POST.get("characteristic_name", "").strip()
    tolerance_str = request.POST.get("tolerance", "0.2000")

    gauge = get_object_or_404(Gauge, id=gauge_id)
    part = get_object_or_404(Part, id=part_id)

    # Generate next study number
    year = timezone.now().year
    prefix = f"MSA-{year}-"
    last_msa = MsaStudy.objects.filter(study_number__startswith=prefix).order_by("-study_number").first()
    seq = (int(last_msa.study_number.split("-")[-1]) + 1) if last_msa else 1
    study_number = f"{prefix}{seq:04d}"

    # Generate synthetic 10 parts x 3 operators x 3 trials with acceptable measurement system
    # Variation centered around 10.0mm with small gage error
    import random
    raw_matrix = []
    base_nominal = 12.50
    for _ in range(10):
        part_offset = random.uniform(-0.06, 0.06)
        part_row = []
        for _ in range(3):
            op_bias = random.uniform(-0.005, 0.005)
            trials = [
                round(base_nominal + part_offset + op_bias + random.gauss(0, 0.003), 4)
                for _ in range(3)
            ]
            part_row.append(trials)
        raw_matrix.append(part_row)

    study = MsaStudy.objects.create(
        study_number=study_number,
        gauge=gauge,
        part=part,
        characteristic_name=characteristic or "Wall Thickness (Dimension A)",
        tolerance=Decimal(tolerance_str),
        part_count=10,
        operator_count=3,
        trial_count=3,
        raw_data=raw_matrix,
    )

    compute_anova_gauge_rr(study.id)
    messages.success(request, f"MSA Study {study.study_number} generated and calculated.")
    return redirect("metrology:msa_detail", study_id=study.id)
