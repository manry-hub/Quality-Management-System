from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponseBadRequest
from apps.master_data.models import ResinMaterial
from .models.sqa import (
    Supplier,
    CertificateOfAnalysis,
    SupplierTierChoices,
    SupplierStatusChoices,
    CoaStatusChoices,
)
from .services import ingest_supplier_coa


def sqa_dashboard_view(request):
    status_filter = request.GET.get("status")
    tier_filter = request.GET.get("tier")

    suppliers_qs = Supplier.objects.prefetch_related("scorecards", "coas").all()
    if status_filter:
        suppliers_qs = suppliers_qs.filter(status=status_filter)
    if tier_filter:
        suppliers_qs = suppliers_qs.filter(tier=tier_filter)

    suppliers = list(suppliers_qs)
    coas = CertificateOfAnalysis.objects.select_related("supplier", "material").order_by("-created_at")[:15]
    materials = ResinMaterial.objects.all().order_by("material_code")

    # Metrics
    total_suppliers = Supplier.objects.count()
    approved_count = Supplier.objects.filter(status=SupplierStatusChoices.APPROVED).count()
    conditional_count = Supplier.objects.filter(status=SupplierStatusChoices.CONDITIONAL).count()
    total_coas = CertificateOfAnalysis.objects.count()

    context = {
        "suppliers": suppliers,
        "coas": coas,
        "materials": materials,
        "total_suppliers": total_suppliers,
        "approved_count": approved_count,
        "conditional_count": conditional_count,
        "total_coas": total_coas,
        "status_filter": status_filter,
        "tier_filter": tier_filter,
        "tier_choices": SupplierTierChoices.choices,
        "status_choices": SupplierStatusChoices.choices,
    }
    return render(request, "sqa/index.html", context)


def supplier_detail_view(request, supplier_id):
    supplier = get_object_or_404(
        Supplier.objects.prefetch_related("scorecards", "coas"),
        id=supplier_id,
    )
    scorecards = list(supplier.scorecards.order_by("-created_at"))
    coas = list(supplier.coas.select_related("material").order_by("-created_at"))

    context = {
        "supplier": supplier,
        "scorecards": scorecards,
        "coas": coas,
    }
    return render(request, "sqa/supplier_detail.html", context)


def coa_validate_view(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required.")

    coa_number = request.POST.get("coa_number", "").strip()
    supplier_id = request.POST.get("supplier_id")
    material_id = request.POST.get("material_id")
    lot_number = request.POST.get("lot_number", "").strip()
    mfg_date = request.POST.get("manufacture_date")
    moisture_str = request.POST.get("moisture_pct", "").strip()
    mfi_str = request.POST.get("mfi_g_10min", "").strip()
    density_str = request.POST.get("density_g_cm3", "").strip()

    if not coa_number or not supplier_id or not material_id or not lot_number or not mfg_date:
        messages.error(request, "Missing mandatory Certificate of Analysis fields.")
        return redirect("sqa:index")

    supplier = get_object_or_404(Supplier, id=supplier_id)
    material = get_object_or_404(ResinMaterial, id=material_id)

    parameters = {}
    if moisture_str:
        try:
            parameters["moisture_pct"] = float(moisture_str)
        except ValueError:
            pass
    if mfi_str:
        try:
            parameters["mfi_g_10min"] = float(mfi_str)
        except ValueError:
            pass
    if density_str:
        try:
            parameters["density_g_cm3"] = float(density_str)
        except ValueError:
            pass

    coa = ingest_supplier_coa(
        coa_number=coa_number,
        supplier=supplier,
        material=material,
        lot_number=lot_number,
        manufacture_date=mfg_date,
        parameters=parameters,
        user=request.user if request.user.is_authenticated else None,
    )

    if coa.status == CoaStatusChoices.APPROVED:
        messages.success(
            request,
            f"CoA {coa.coa_number} for lot {coa.lot_number} verified COMPLIANT (Score: {coa.compliance_score}%).",
        )
    else:
        messages.warning(
            request,
            f"CoA {coa.coa_number} for lot {coa.lot_number} REJECTED due to spec deviation: {coa.deviation_notes}",
        )

    return redirect("sqa:index")
