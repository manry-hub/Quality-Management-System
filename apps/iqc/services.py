from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from apps.core.models.audit import AuditTrailEvent
from apps.core.models.outbox import OutboxEvent
from apps.master_data.models.material import ResinMaterial
from .models.iqc_task import IqcInspectionTask, IqcSample


def evaluate_coa_parameters(
    material: ResinMaterial,
    moisture_pct: Decimal | float | None,
    mfi_value: Decimal | float | None,
    density: Decimal | float | None = None,
) -> tuple[bool, list[str]]:
    """
    Evaluates CoA chemical & physical properties against Master Data specs.
    Moisture content must be <= material.target_moisture_max_pct (e.g. 0.02%).
    MFI must be within target +/- tolerance (e.g. 18 +/- 2 g/10min).
    """
    issues = []

    if moisture_pct is not None:
        moisture = Decimal(str(moisture_pct))
        if moisture > material.target_moisture_max_pct:
            issues.append(
                f"Moisture {moisture:.4f}% exceeds maximum allowable {material.target_moisture_max_pct:.4f}%"
            )

    if mfi_value is not None:
        mfi = Decimal(str(mfi_value))
        min_mfi = material.target_mfi_nominal - material.target_mfi_tolerance
        max_mfi = material.target_mfi_nominal + material.target_mfi_tolerance
        if mfi < min_mfi or mfi > max_mfi:
            issues.append(
                f"MFI {mfi:.2f} g/10min is outside allowable tolerance [{min_mfi:.2f} - {max_mfi:.2f}]"
            )

    is_valid = len(issues) == 0
    return is_valid, issues


@transaction.atomic
def process_wms_inbound_shipment(payload: dict) -> IqcInspectionTask:
    """
    Handles dock receiving webhook from companion WMS.
    Idempotent on wms_event_id.
    """
    wms_event_id = payload.get("wms_event_id")
    if not wms_event_id:
        raise ValueError("Missing required wms_event_id")

    existing = IqcInspectionTask.objects.filter(wms_event_id=wms_event_id).first()
    if existing:
        return existing

    material_code = payload.get("material_code")
    try:
        material = ResinMaterial.objects.get(material_code=material_code)
    except ResinMaterial.DoesNotExist:
        raise ValueError(f"Unknown resin material code: {material_code}")

    task = IqcInspectionTask.objects.create(
        wms_event_id=wms_event_id,
        lot_number=payload.get("lot_number", f"LOT-{wms_event_id[:8]}"),
        material=material,
        supplier_code=payload.get("supplier_code", "VEND-UNKNOWN"),
        quantity_kg=Decimal(str(payload.get("quantity_kg", "1000.00"))),
        status="PENDING_INSPECTION",
        disposition="NONE",
        coa_file_path=payload.get("coa_file_path", ""),
    )

    # Pre-populate sample records if barcodes are provided
    barcodes = payload.get("pallet_barcodes", [])
    for idx, barcode in enumerate(barcodes, start=1):
        IqcSample.objects.create(
            task=task,
            sample_number=idx,
            bag_pallet_barcode=barcode,
        )

    AuditTrailEvent.objects.create(
        user=None,
        badge_number="WMS-GATEWAY",
        action_type="CREATE",
        entity_type="IqcInspectionTask",
        entity_id=task.id,
        payload_snapshot={
            "wms_event_id": wms_event_id,
            "lot_number": task.lot_number,
            "material": material_code,
            "quantity_kg": str(task.quantity_kg),
        },
        signature_manifestation="WMS Inbound Dock Intake Webhook",
    )

    return task


@transaction.atomic
def submit_iqc_disposition(
    task: IqcInspectionTask,
    inspector,
    disposition: str,
    coa_moisture: Decimal | float | None = None,
    coa_mfi: Decimal | float | None = None,
    physical_moisture: Decimal | float | None = None,
    physical_mfi: Decimal | float | None = None,
    rejection_reason: str = "",
) -> IqcInspectionTask:
    """
    Executes inspection evaluation, updates task status, and atomically dispatches
    Transactional Outbox events to WMS (qms.lot_released or qms.sncr_created).
    """
    task.coa_moisture_pct = (
        Decimal(str(coa_moisture)) if coa_moisture is not None else None
    )
    task.coa_mfi_value = Decimal(str(coa_mfi)) if coa_mfi is not None else None
    task.physical_moisture_pct = (
        Decimal(str(physical_moisture)) if physical_moisture is not None else None
    )
    task.physical_mfi_value = (
        Decimal(str(physical_mfi)) if physical_mfi is not None else None
    )

    effective_moisture = (
        task.physical_moisture_pct
        if task.physical_moisture_pct is not None
        else task.coa_moisture_pct
    )
    effective_mfi = (
        task.physical_mfi_value
        if task.physical_mfi_value is not None
        else task.coa_mfi_value
    )

    is_conforming, issues = evaluate_coa_parameters(
        task.material, effective_moisture, effective_mfi
    )

    if disposition == "RELEASE_TO_AVAILABLE":
        if not is_conforming:
            raise ValueError(
                f"Cannot accept lot: Resin parameters violate specification: {'; '.join(issues)}"
            )
        task.status = "ACCEPTED"
        task.disposition = "RELEASE_TO_AVAILABLE"
        task.rejection_reason = ""

        # Emit Transactional Outbox Event to WMS
        OutboxEvent.objects.create(
            event_type="qms.lot_released",
            destination_system="WMS",
            payload={
                "wms_event_id": task.wms_event_id,
                "lot_number": task.lot_number,
                "material_code": task.material.material_code,
                "quantity_kg": str(task.quantity_kg),
                "status": "AVAILABLE",
                "released_at": timezone.now().isoformat(),
                "inspector_badge": (
                    getattr(inspector, "badge_number", "AUTO-QA")
                    if inspector
                    else "AUTO-QA"
                ),
            },
        )
    elif disposition == "QUARANTINE_REJECTED":
        task.status = "REJECTED"
        task.disposition = "QUARANTINE_REJECTED"
        task.rejection_reason = (
            rejection_reason or "; ".join(issues) or "Failed IQC criteria"
        )

        # Emit Transactional Outbox Event to WMS (Supplier NCR)
        OutboxEvent.objects.create(
            event_type="qms.sncr_created",
            destination_system="WMS",
            payload={
                "wms_event_id": task.wms_event_id,
                "lot_number": task.lot_number,
                "material_code": task.material.material_code,
                "supplier_code": task.supplier_code,
                "quantity_kg": str(task.quantity_kg),
                "status": "QUARANTINE",
                "rejection_reason": task.rejection_reason,
                "inspector_badge": (
                    getattr(inspector, "badge_number", "AUTO-QA")
                    if inspector
                    else "AUTO-QA"
                ),
            },
        )
    else:
        raise ValueError(f"Invalid IQC disposition: {disposition}")

    task.inspected_by = inspector
    task.inspected_at = timezone.now()
    task.save()

    badge = getattr(inspector, "badge_number", "AUTO-QA") if inspector else "AUTO-QA"
    AuditTrailEvent.objects.create(
        user=inspector if getattr(inspector, "is_authenticated", False) else None,
        badge_number=badge,
        action_type="DISPOSITION",
        entity_type="IqcInspectionTask",
        entity_id=task.id,
        payload_snapshot={
            "status": task.status,
            "disposition": task.disposition,
            "rejection_reason": task.rejection_reason,
            "moisture_pct": str(effective_moisture) if effective_moisture else None,
            "mfi_value": str(effective_mfi) if effective_mfi else None,
        },
        signature_manifestation=f"IQC disposition submitted: {task.disposition}",
    )

    return task
