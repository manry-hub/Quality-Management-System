from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponseBadRequest
from apps.master_data.models import Part
from .models.vision import (
    VisionInspectionStation,
    VisionDefectInspection,
    DefectTypeChoices,
    DefectSeverityChoices,
    VisionActionChoices,
)
from .services import classify_molding_defect


def vision_console_view(request):
    stations = list(VisionInspectionStation.objects.all())
    inspections = list(
        VisionDefectInspection.objects.select_related("station", "part", "ncr").order_by("-inspection_timestamp")[:25]
    )
    parts = list(Part.objects.all().order_by("part_number"))

    # Metrics
    total_inspections = VisionDefectInspection.objects.count()
    defect_count = VisionDefectInspection.objects.exclude(primary_defect_type=DefectTypeChoices.NO_DEFECT).count()
    hold_triggered_count = VisionDefectInspection.objects.filter(
        auto_action_taken=VisionActionChoices.NCR_HOLD_TRIGGERED
    ).count()
    online_stations = sum(1 for s in stations if s.is_online)

    defect_breakdown = {}
    for choice, label in DefectTypeChoices.choices:
        if choice != DefectTypeChoices.NO_DEFECT:
            cnt = VisionDefectInspection.objects.filter(primary_defect_type=choice).count()
            defect_breakdown[label] = cnt

    context = {
        "stations": stations,
        "inspections": inspections,
        "parts": parts,
        "total_inspections": total_inspections,
        "defect_count": defect_count,
        "hold_triggered_count": hold_triggered_count,
        "online_stations": online_stations,
        "defect_breakdown": defect_breakdown,
        "defect_types": DefectTypeChoices.choices,
        "severity_choices": DefectSeverityChoices.choices,
    }
    return render(request, "vision/index.html", context)


def vision_station_detail_view(request, station_id):
    station = get_object_or_404(VisionInspectionStation, id=station_id)
    inspections = list(station.inspections.select_related("part", "ncr").order_by("-inspection_timestamp")[:30])

    context = {
        "station": station,
        "inspections": inspections,
    }
    return render(request, "vision/station_detail.html", context)


def vision_simulate_shot_view(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required.")

    station_id = request.POST.get("station_id")
    part_id = request.POST.get("part_id")
    defect_type = request.POST.get("defect_type", DefectTypeChoices.NO_DEFECT)
    severity = request.POST.get("severity", DefectSeverityChoices.ACCEPTABLE)
    confidence_str = request.POST.get("confidence_score", "0.95")
    shot_num_str = request.POST.get("shot_number", "101")
    cavity_str = request.POST.get("cavity_number", "1")

    station = get_object_or_404(VisionInspectionStation, id=station_id)
    part = get_object_or_404(Part, id=part_id)

    try:
        confidence = float(confidence_str)
        shot_num = int(shot_num_str)
        cavity_num = int(cavity_str)
    except (ValueError, TypeError):
        confidence = 0.95
        shot_num = 1
        cavity_num = 1

    simulated_boxes = []
    if defect_type != DefectTypeChoices.NO_DEFECT:
        simulated_boxes.append({
            "label": defect_type,
            "bbox": [150, 110, 80, 35],
            "confidence": confidence,
            "severity": severity,
        })

    inspection = classify_molding_defect(
        station=station,
        part=part,
        shot_number=shot_num,
        cavity_number=cavity_num,
        simulated_detections=simulated_boxes,
        image_path="simulated/camera/shot_feed.jpg",
        user=request.user if request.user.is_authenticated else None,
    )

    if inspection.auto_action_taken == VisionActionChoices.NCR_HOLD_TRIGGERED:
        messages.error(
            request,
            (
                f"EMERGENCY QUALITY HOLD: Shot #{inspection.shot_number} Cavity #{inspection.cavity_number} "
                f"triggered automated NCR ({inspection.ncr.ncr_number}) due to "
                f"CRITICAL {inspection.primary_defect_type}."
            ),
        )
    elif inspection.auto_action_taken == VisionActionChoices.REJECT_DIVERTED:
        messages.warning(
            request,
            (
                f"REJECT DIVERTED: Shot #{inspection.shot_number} Cavity #{inspection.cavity_number} "
                f"classified as {inspection.primary_defect_type} ({inspection.severity}). Diverted to scrap."
            ),
        )
    else:
        messages.success(
            request,
            (
                f"Shot #{inspection.shot_number} Cavity #{inspection.cavity_number} CLEARED: "
                "Clean shot conforming to quality specs."
            ),
        )

    return redirect("vision:index")
