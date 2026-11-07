from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models.iqc_task import IqcInspectionTask
from .services import submit_iqc_disposition


def iqc_index_view(request):
    """
    Incoming Quality Control (IQC) Receiving Terminal.
    Displays active resin dock receiving queue and laboratory verification forms.
    """
    status_filter = request.GET.get("status", "")
    tasks = IqcInspectionTask.objects.select_related("material").all()
    if status_filter:
        tasks = tasks.filter(status=status_filter)

    pending_count = IqcInspectionTask.objects.filter(status="PENDING_INSPECTION").count()
    accepted_count = IqcInspectionTask.objects.filter(status="ACCEPTED").count()
    rejected_count = IqcInspectionTask.objects.filter(status="REJECTED").count()

    context = {
        "title": "Incoming Quality Control (IQC)",
        "subTitle": "Raw Resin & Chemical Verification Terminal",
        "tasks": tasks,
        "pending_count": pending_count,
        "accepted_count": accepted_count,
        "rejected_count": rejected_count,
        "status_filter": status_filter,
    }
    return render(request, "iqc/index.html", context)


def iqc_disposition_view(request, task_id):
    """
    Handles IQC laboratory test entry and material release/quarantine disposition.
    """
    task = get_object_or_404(IqcInspectionTask, id=task_id)

    if request.method == "POST":
        disposition = request.POST.get("disposition")
        moisture_str = request.POST.get("moisture_pct")
        mfi_str = request.POST.get("mfi_value")
        reason = request.POST.get("rejection_reason", "")

        moisture = Decimal(moisture_str) if moisture_str else None
        mfi = Decimal(mfi_str) if mfi_str else None

        try:
            inspector = request.user if request.user.is_authenticated else None
            submit_iqc_disposition(
                task=task,
                inspector=inspector,
                disposition=disposition,
                physical_moisture=moisture,
                physical_mfi=mfi,
                rejection_reason=reason,
            )
            if disposition == "RELEASE_TO_AVAILABLE":
                messages.success(
                    request,
                    f"Lot {task.lot_number} APPROVED and released to WMS Available inventory."
                )
            else:
                messages.warning(
                    request,
                    f"Lot {task.lot_number} REJECTED and quarantined. Supplier NCR created."
                )
        except Exception as e:
            messages.error(request, f"Disposition error: {str(e)}")

    return redirect("iqc:index")
