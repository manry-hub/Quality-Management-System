from decimal import Decimal
import hashlib
import hmac
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from apps.core.models.audit import AuditTrailEvent
from apps.core.models.outbox import OutboxEvent
from .models.ipqc_inspection import IpqcInspection
from .models.telemetry import TelemetrySummary


def generate_fai_signature_token(
    inspection_id: str,
    mes_run_id: str,
    machine_code: str,
    inspector_badge: str,
    timestamp_str: str,
) -> str:
    """
    Generates a cryptographically signed HMAC-SHA256 release token
    for MES First-Piece Inspection clearance.
    """
    secret = getattr(settings, "MES_INTEGRATION_SECRET", settings.SECRET_KEY).encode("utf-8")
    message = f"{inspection_id}:{mes_run_id}:{machine_code}:{inspector_badge}:{timestamp_str}".encode("utf-8")
    return hmac.new(secret, message, hashlib.sha256).hexdigest()


@transaction.atomic
def evaluate_and_release_fai(
    inspection: IpqcInspection,
    inspector,
) -> tuple[bool, str, str]:
    """
    Evaluates cavity sample conformity and issues a cryptographic FAI release token.
    Sub-200ms hard-gating execution.
    """
    samples = list(inspection.cavity_samples.all())
    if not samples:
        return False, "", "No cavity samples provided for FAI inspection"

    non_conforming = [s for s in samples if not s.is_conforming]
    badge = getattr(inspector, "badge_number", "AUTO-QA") if inspector else "AUTO-QA"
    now = timezone.now()
    now_str = now.isoformat()

    if non_conforming:
        inspection.disposition = "REJECTED"
        inspection.line_stop_triggered = True
        inspection.line_stop_reason = (
            f"FAI Rejected: {len(non_conforming)} cavity samples out of tolerance"
        )
        inspection.inspected_by = inspector
        inspection.save()

        OutboxEvent.objects.create(
            event_type="qms.fai_rejected",
            destination_system="MES",
            payload={
                "mes_run_id": inspection.mes_run_id,
                "machine_code": inspection.machine_code,
                "status": "REJECTED",
                "reason": inspection.line_stop_reason,
                "inspector_badge": badge,
                "timestamp": now_str,
            },
        )

        AuditTrailEvent.objects.create(
            user=inspector if getattr(inspector, "is_authenticated", False) else None,
            badge_number=badge,
            action_type="DISPOSITION",
            entity_type="IpqcInspection",
            entity_id=inspection.id,
            payload_snapshot={
                "disposition": "REJECTED",
                "mes_run_id": inspection.mes_run_id,
                "machine_code": inspection.machine_code,
                "failed_samples": len(non_conforming),
            },
            signature_manifestation="First-Piece Inspection rejected",
        )

        return False, "", inspection.line_stop_reason

    # All samples conforming: generate cryptographic release token
    token = generate_fai_signature_token(
        str(inspection.id),
        inspection.mes_run_id,
        inspection.machine_code,
        badge,
        now_str,
    )

    inspection.disposition = "RELEASED"
    inspection.signature_token = token
    inspection.signed_at = now
    inspection.line_stop_triggered = False
    inspection.inspected_by = inspector
    inspection.save()

    # Emit Transactional Outbox Event to MES for sub-200ms dispatch
    OutboxEvent.objects.create(
        event_type="qms.fai_released",
        destination_system="MES",
        payload={
            "mes_run_id": inspection.mes_run_id,
            "machine_code": inspection.machine_code,
            "status": "APPROVED",
            "signature_token": token,
            "inspector_badge": badge,
            "signed_at": now_str,
        },
    )

    AuditTrailEvent.objects.create(
        user=inspector if getattr(inspector, "is_authenticated", False) else None,
        badge_number=badge,
        action_type="QA_RELEASE",
        entity_type="IpqcInspection",
        entity_id=inspection.id,
        payload_snapshot={
            "disposition": "RELEASED",
            "mes_run_id": inspection.mes_run_id,
            "machine_code": inspection.machine_code,
            "token": token,
        },
        signature_manifestation="First-Piece Inspection approved & cryptographic token issued",
    )

    return True, token, "FAI Approved and cryptographic release dispatched to MES"


@transaction.atomic
def process_cycle_telemetry(payload: dict) -> TelemetrySummary:
    """
    Ingests pre-aggregated shot cycle summary from MES.
    Evaluates screw cushion drift (+/- 0.5mm window).
    If 3 consecutive shots drift beyond +/- 0.5mm, trips Andon line stop.
    """
    machine_code = payload.get("machine_code")
    if not machine_code:
        raise ValueError("Missing machine_code in telemetry payload")

    cushion = Decimal(str(payload.get("cushion_mm", "5.0")))
    cushion_nominal = Decimal(str(payload.get("cushion_nominal_mm", "5.0")))
    drift = abs(cushion - cushion_nominal)
    is_drift_alert = drift > Decimal("0.500")

    summary = TelemetrySummary.objects.create(
        machine_code=machine_code,
        mold_code=payload.get("mold_code", "MOLD-DEFAULT"),
        mes_run_id=payload.get("mes_run_id", "RUN-DEFAULT"),
        shot_number=int(payload.get("shot_number", 1)),
        cushion_mm=cushion,
        peak_pressure_bar=Decimal(str(payload.get("peak_pressure_bar", "1200.00"))),
        fill_time_s=Decimal(str(payload.get("fill_time_s", "2.500"))),
        cycle_time_s=Decimal(str(payload.get("cycle_time_s", "35.00"))),
        cushion_nominal_mm=cushion_nominal,
        cushion_drift_alert=is_drift_alert,
    )

    # Check last 3 consecutive shots on this machine
    recent_shots = list(
        TelemetrySummary.objects.filter(machine_code=machine_code)
        .order_by("-created_at")[:3]
    )

    if len(recent_shots) == 3 and all(s.cushion_drift_alert for s in recent_shots):
        # Trigger Andon Line Stop event to MES
        OutboxEvent.objects.create(
            event_type="qms.andon_line_stop",
            destination_system="MES",
            payload={
                "machine_code": machine_code,
                "mes_run_id": summary.mes_run_id,
                "reason": (
                    f"Process window drift: Screw cushion deviated by {drift:.3f}mm "
                    f"(limit +/-0.5mm) across 3 consecutive cycles"
                ),
                "latest_cushion_mm": str(cushion),
                "nominal_cushion_mm": str(cushion_nominal),
                "shot_number": summary.shot_number,
                "timestamp": timezone.now().isoformat(),
            },
        )

        AuditTrailEvent.objects.create(
            user=None,
            badge_number="ANDON-DAEMON",
            action_type="QA_HOLD",
            entity_type="TelemetrySummary",
            entity_id=None,
            payload_snapshot={
                "telemetry_summary_id": summary.id,
                "machine_code": machine_code,
                "mes_run_id": summary.mes_run_id,
                "reason": "3 consecutive shots outside cushion +/-0.5mm window",
            },
            signature_manifestation="Automated injection telemetry containment line stop",
        )

    return summary
