from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from apps.ipqc.models.ipqc_inspection import IpqcInspection
from apps.ipqc.models.telemetry import TelemetrySummary
from apps.ipqc.services import evaluate_and_release_fai


def ipqc_index_view(request):
    """
    In-Process Quality Control (IPQC) Machine Surveillance Terminal.
    Monitors 10 injection molding machines (IMM-01 to IMM-10), FAI hard-gating,
    and screw cushion telemetry.
    """
    machines = [f"IMM-{i:02d}" for i in range(1, 11)]
    machine_status_list = []

    for m in machines:
        latest_shot = TelemetrySummary.objects.filter(machine_code=m).order_by("-created_at").first()
        active_fai = IpqcInspection.objects.filter(machine_code=m).order_by("-created_at").first()

        is_andon = latest_shot.cushion_drift_alert if latest_shot else False
        is_fai_released = active_fai.disposition == "RELEASED" if active_fai else False

        machine_status_list.append({
            "code": m,
            "latest_shot": latest_shot,
            "active_fai": active_fai,
            "is_andon": is_andon,
            "is_fai_released": is_fai_released,
        })

    inspections = IpqcInspection.objects.select_related("part").all()[:15]

    context = {
        "title": "In-Process Quality Control (IPQC)",
        "subTitle": "Machine Gating & Real-Time Telemetry Monitor",
        "machines": machine_status_list,
        "inspections": inspections,
    }
    return render(request, "ipqc/index.html", context)


def ipqc_fai_approve_view(request, inspection_id):
    """
    Submits First-Piece Inspection (FAI) approval and dispatches
    cryptographic release token to MES.
    """
    inspection = get_object_or_404(IpqcInspection, id=inspection_id)

    if request.method == "POST":
        inspector = request.user if request.user.is_authenticated else None
        approved, token, message = evaluate_and_release_fai(inspection, inspector)
        if approved:
            messages.success(
                request,
                f"FAI Approved for {inspection.machine_code}! Token dispatched to MES: {token[:16]}..."
            )
        else:
            messages.error(request, f"FAI Sign-off Rejected: {message}")

    return redirect("ipqc:index")
