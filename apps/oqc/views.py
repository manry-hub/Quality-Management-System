import os
from django.conf import settings
from django.http import HttpResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models.oqc_inspection import OqcInspection
from .services import evaluate_and_release_oqc


def oqc_index_view(request):
    """
    Outgoing Quality Control (OQC) Clearance Terminal.
    Enforces ISO 2859-1 Level II c=0 acceptance sampling and CoC release.
    """
    inspections = OqcInspection.objects.select_related("part").all()

    total_count = inspections.count()
    released_count = inspections.filter(status="RELEASED_FOR_SHIPMENT").count()
    rejected_count = inspections.filter(status="REJECTED").count()
    pending_count = inspections.filter(status="PENDING").count()

    context = {
        "title": "Outgoing Quality Control (OQC)",
        "subTitle": "ISO 2859-1 (c=0) Sampling & CoC Clearance Terminal",
        "inspections": inspections,
        "total_count": total_count,
        "released_count": released_count,
        "rejected_count": rejected_count,
        "pending_count": pending_count,
    }
    return render(request, "oqc/index.html", context)


def oqc_release_view(request, inspection_id):
    """
    Evaluates zero-defect criterion and releases finished goods pallet for shipment.
    """
    inspection = get_object_or_404(OqcInspection, id=inspection_id)

    if request.method == "POST":
        defects = int(request.POST.get("defects_found", 0))
        box_intact = request.POST.get("box_intact") == "on"
        esd_sealed = request.POST.get("esd_sealed") == "on"
        desiccant = request.POST.get("desiccant") == "on"
        datamatrix = request.POST.get("datamatrix") == "on"

        inspection.defects_found = defects
        inspection.packaging_box_intact = box_intact
        inspection.esd_bag_sealed = esd_sealed
        inspection.desiccant_present = desiccant
        inspection.datamatrix_verified = datamatrix

        inspector = request.user if request.user.is_authenticated else None
        released, coc_number, message = evaluate_and_release_oqc(inspection, inspector)

        if released:
            messages.success(
                request,
                f"Pallet {inspection.pallet_barcode} APPROVED! Certificate of Conformance {coc_number} released to WMS."
            )
        else:
            messages.error(
                request,
                f"Pallet {inspection.pallet_barcode} REJECTED from shipment: {message}"
            )

    return redirect("oqc:index")


def oqc_view_coc(request, inspection_id):
    """
    Displays the generated Certificate of Conformance (CoC) document.
    """
    inspection = get_object_or_404(OqcInspection, id=inspection_id)
    if not inspection.coc_file_path:
        raise Http404("Certificate of Conformance has not been generated for this lot.")

    full_path = os.path.join(settings.MEDIA_ROOT, inspection.coc_file_path)
    if not os.path.exists(full_path):
        raise Http404("CoC document file not found on disk.")

    with open(full_path, "r", encoding="utf-8") as f:
        content = f.read()

    return HttpResponse(content, content_type="text/html")
