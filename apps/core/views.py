import json
from django.shortcuts import render
from apps.core.models.audit import AuditTrailEvent
from apps.iqc.models.iqc_task import IqcInspectionTask
from apps.ipqc.models.ipqc_inspection import IpqcInspection
from apps.ipqc.models.telemetry import TelemetrySummary
from apps.oqc.models.oqc_inspection import OqcInspection


def dashboard_view(request):
    """
    Executive Quality & Plant Andon Control Dashboard.
    Aggregates metrics across IQC, IPQC FAI gating, Telemetry Drift, and OQC.
    """
    # 1. IQC Metrics
    iqc_total = IqcInspectionTask.objects.count()
    iqc_accepted = IqcInspectionTask.objects.filter(status="ACCEPTED").count()
    iqc_rejected = IqcInspectionTask.objects.filter(status="REJECTED").count()
    iqc_pending = IqcInspectionTask.objects.filter(status="PENDING_INSPECTION").count()
    iqc_rate = (
        round((iqc_accepted / iqc_total) * 100, 1) if iqc_total > 0 else 100.0
    )

    # 2. IPQC & Telemetry Metrics
    ipqc_fai_approved = IpqcInspection.objects.filter(disposition="RELEASED").count()
    ipqc_fai_pending = IpqcInspection.objects.filter(disposition="PENDING").count()
    andon_alerts = TelemetrySummary.objects.filter(cushion_drift_alert=True).count()
    active_machines_count = (
        TelemetrySummary.objects.values("machine_code").distinct().count() or 1
    )

    # 3. OQC Clearance Metrics
    oqc_total = OqcInspection.objects.count()
    oqc_released = OqcInspection.objects.filter(status="RELEASED_FOR_SHIPMENT").count()
    oqc_rejected = OqcInspection.objects.filter(status="REJECTED").count()
    oqc_pending = OqcInspection.objects.filter(status="PENDING").count()
    oqc_compliance_rate = (
        round((oqc_released / oqc_total) * 100, 1) if oqc_total > 0 else 100.0
    )

    # 4. Telemetry Chart Data (Last 15 shots for screw cushion monitor)
    recent_shots = list(
        TelemetrySummary.objects.order_by("-created_at")[:15]
    )
    recent_shots.reverse()

    shot_labels = [f"#{s.shot_number}" for s in recent_shots] or ["#1", "#2", "#3"]
    cushion_values = [
        float(s.cushion_mm) for s in recent_shots
    ] or [5.0, 5.1, 5.05]
    usl_line = [5.5] * len(shot_labels)
    lsl_line = [4.5] * len(shot_labels)
    nominal_line = [5.0] * len(shot_labels)

    # 5. Recent 21 CFR Part 11 Audit Trail
    audit_events = AuditTrailEvent.objects.order_by("-timestamp")[:8]

    # 6. Recent Operational Inspections
    recent_iqc = IqcInspectionTask.objects.select_related("material").order_by("-created_at")[:5]
    recent_ipqc = IpqcInspection.objects.select_related("part").order_by("-created_at")[:5]
    recent_oqc = OqcInspection.objects.select_related("part").order_by("-created_at")[:5]

    context = {
        "title": "Quality Executive Control",
        "subTitle": "Automotive Injection Molding Plant #01",
        "iqc_total": iqc_total,
        "iqc_accepted": iqc_accepted,
        "iqc_rejected": iqc_rejected,
        "iqc_pending": iqc_pending,
        "iqc_rate": iqc_rate,
        "ipqc_fai_approved": ipqc_fai_approved,
        "ipqc_fai_pending": ipqc_fai_pending,
        "active_machines_count": active_machines_count,
        "andon_alerts": andon_alerts,
        "oqc_total": oqc_total,
        "oqc_released": oqc_released,
        "oqc_rejected": oqc_rejected,
        "oqc_pending": oqc_pending,
        "oqc_compliance_rate": oqc_compliance_rate,
        "shot_labels_json": json.dumps(shot_labels),
        "cushion_values_json": json.dumps(cushion_values),
        "usl_line_json": json.dumps(usl_line),
        "lsl_line_json": json.dumps(lsl_line),
        "nominal_line_json": json.dumps(nominal_line),
        "audit_events": audit_events,
        "recent_iqc": recent_iqc,
        "recent_ipqc": recent_ipqc,
        "recent_oqc": recent_oqc,
    }

    return render(request, "dashboard/index.html", context)
