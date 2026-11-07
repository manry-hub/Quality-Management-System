from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models.ncr import (
    NonConformanceReport,
    SourceDomain,
    SeverityLevel,
    TargetType,
    NcrStatus,
)
from .services import declare_quality_hold, close_ncr


def ncr_list_view(request):
    """
    Non-Conformance Report (NCR) & Enterprise Quality Hold Ledger.
    Provides centralized containment tracking across IQC, IPQC, OQC, and Customer RMA.
    """
    status_filter = request.GET.get("status", "")
    severity_filter = request.GET.get("severity", "")

    ncrs = NonConformanceReport.objects.select_related("created_by").all()
    if status_filter:
        ncrs = ncrs.filter(status=status_filter)
    if severity_filter:
        ncrs = ncrs.filter(severity=severity_filter)

    total_ncrs = NonConformanceReport.objects.count()
    active_holds_count = NonConformanceReport.objects.filter(hold_declared=True).count()
    critical_count = NonConformanceReport.objects.filter(severity=SeverityLevel.CRITICAL).count()
    closed_count = NonConformanceReport.objects.filter(status=NcrStatus.CLOSED).count()

    context = {
        "title": "Non-Conformance & Quality Hold Ledger",
        "subTitle": "Multi-System Containment & IATF 16949 Quarantine Control",
        "ncrs": ncrs,
        "total_ncrs": total_ncrs,
        "active_holds_count": active_holds_count,
        "critical_count": critical_count,
        "closed_count": closed_count,
        "status_filter": status_filter,
        "severity_filter": severity_filter,
        "source_domains": SourceDomain.choices,
        "severities": SeverityLevel.choices,
        "target_types": TargetType.choices,
    }
    return render(request, "ncr/index.html", context)


def ncr_declare_hold_view(request):
    """
    Declares an active Quality Hold and issues an NCR with multi-system outbox broadcast.
    """
    if request.method == "POST":
        source_domain = request.POST.get("source_domain", SourceDomain.IPQC)
        severity = request.POST.get("severity", SeverityLevel.MAJOR)
        target_type = request.POST.get("target_type", TargetType.IN_PROCESS_RUN)
        target_identifier = request.POST.get("target_identifier", "").strip()
        defect_description = request.POST.get("defect_description", "").strip()
        containment_actions = request.POST.get("containment_actions", "").strip()
        badge_number = request.POST.get("badge_number", "").strip()

        if not target_identifier or not defect_description:
            messages.error(request, "Target identifier and defect description are required.")
            return redirect("ncr:index")

        user = request.user if request.user.is_authenticated else None
        ncr = declare_quality_hold(
            source_domain=source_domain,
            severity=severity,
            target_type=target_type,
            target_identifier=target_identifier,
            defect_description=defect_description,
            containment_actions=containment_actions,
            user=user,
            badge_number=badge_number,
        )
        messages.success(
            request,
            f"Quality Hold declared: {ncr.ncr_number} locked {ncr.target_identifier} across MES/WMS."
        )
    return redirect("ncr:index")


def ncr_close_view(request, ncr_id):
    """
    Closes an existing NCR with verification notes and 21 CFR 11 audit manifestation.
    """
    ncr = get_object_or_404(NonConformanceReport, id=ncr_id)
    if request.method == "POST":
        resolution_notes = request.POST.get("resolution_notes", "").strip()
        badge_number = request.POST.get("badge_number", "").strip()

        if not resolution_notes:
            messages.error(request, "Resolution notes are required to close an NCR.")
            return redirect("ncr:index")

        user = request.user if request.user.is_authenticated else None
        close_ncr(
            ncr=ncr,
            resolution_notes=resolution_notes,
            user=user,
            badge_number=badge_number,
        )
        messages.success(request, f"NCR {ncr.ncr_number} marked as CLOSED.")
    return redirect("ncr:index")
