import uuid
from typing import Dict, Any, List, Optional
from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from .models.capa import (
    Capa8dRecord,
    CapaVoeRecord,
    CapaDisciplineChoices,
    CapaStatusChoices,
    VoeMilestoneChoices,
)


def generate_capa_number() -> str:
    """Generates an incremental CAPA tracking number: CAPA-YYYY-XXXX."""
    year = timezone.now().year
    prefix = f"CAPA-{year}-"
    last_capa = (
        Capa8dRecord.objects.filter(capa_number__startswith=prefix)
        .order_by("-capa_number")
        .first()
    )
    if last_capa:
        try:
            last_seq = int(last_capa.capa_number.split("-")[-1])
            next_seq = last_seq + 1
        except (ValueError, IndexError):
            next_seq = 1
    else:
        next_seq = 1
    return f"{prefix}{next_seq:04d}"


@transaction.atomic
def create_8d_capa(
    title: str,
    champion,
    leader,
    d2_problem_statement: str,
    team_members: Optional[List[Dict[str, str]]] = None,
    ncr=None,
    capa_number: Optional[str] = None,
) -> Capa8dRecord:
    """
    Initializes a new 8D CAPA record with D1 team establishment and D2 problem definition.
    """
    if not capa_number:
        capa_number = generate_capa_number()

    if team_members is None:
        team_members = []

    capa = Capa8dRecord.objects.create(
        capa_number=capa_number,
        title=title,
        ncr=ncr,
        champion=champion,
        leader=leader,
        team_members=team_members,
        d2_problem_statement=d2_problem_statement,
        current_discipline=CapaDisciplineChoices.D1_TEAM,
        status=CapaStatusChoices.OPEN,
    )
    return capa


@transaction.atomic
def advance_8d_discipline(
    capa_id: uuid.UUID,
    target_discipline: str,
    data: Dict[str, Any],
) -> Capa8dRecord:
    """
    Progresses an 8D CAPA record through the disciplines D1 through D8,
    persisting associated discipline data and validating stage gates.
    """
    capa = Capa8dRecord.objects.select_for_update().get(id=capa_id)

    if target_discipline == CapaDisciplineChoices.D2_PROBLEM:
        if "d2_problem_statement" in data:
            capa.d2_problem_statement = data["d2_problem_statement"]

    elif target_discipline == CapaDisciplineChoices.D3_CONTAINMENT:
        if "d3_containment_action" in data:
            capa.d3_containment_action = data["d3_containment_action"]
        capa.d3_containment_verified_at = timezone.now()
        capa.status = CapaStatusChoices.IN_PROGRESS

    elif target_discipline == CapaDisciplineChoices.D4_ROOT_CAUSE:
        if "d4_root_cause_5why" in data:
            capa.d4_root_cause_5why = data["d4_root_cause_5why"]
        if "d4_fishbone_data" in data:
            capa.d4_fishbone_data = data["d4_fishbone_data"]
        if "d4_root_cause_summary" in data:
            capa.d4_root_cause_summary = data["d4_root_cause_summary"]

    elif target_discipline == CapaDisciplineChoices.D5_PCA_CHOSEN:
        if "d5_permanent_corrective_actions" in data:
            capa.d5_permanent_corrective_actions = data["d5_permanent_corrective_actions"]

    elif target_discipline == CapaDisciplineChoices.D6_PCA_IMPLEMENTED:
        if "d6_validation_results" in data:
            capa.d6_validation_results = data["d6_validation_results"]
        if "d6_implementation_date" in data:
            capa.d6_implementation_date = data["d6_implementation_date"]
        else:
            capa.d6_implementation_date = timezone.now().date()

    elif target_discipline == CapaDisciplineChoices.D7_PREVENTION:
        if "d7_preventive_actions" in data:
            capa.d7_preventive_actions = data["d7_preventive_actions"]
        if "fmea_updated" in data:
            capa.fmea_updated = bool(data["fmea_updated"])
        if "control_plan_updated" in data:
            capa.control_plan_updated = bool(data["control_plan_updated"])

        # Transition status to Verification of Effectiveness (VoE)
        capa.status = CapaStatusChoices.UNDER_VOE
        base_date = timezone.now().date()

        # Seed 30, 60, and 90-day VoE milestones if not already present
        milestones = [
            (VoeMilestoneChoices.DAY_30, 30),
            (VoeMilestoneChoices.DAY_60, 60),
            (VoeMilestoneChoices.DAY_90, 90),
        ]
        for milestone_code, days_offset in milestones:
            CapaVoeRecord.objects.get_or_create(
                capa=capa,
                milestone=milestone_code,
                defaults={
                    "target_date": base_date + timedelta(days=days_offset),
                    "is_effective": True,
                    "defect_count_in_period": 0,
                },
            )

    elif target_discipline == CapaDisciplineChoices.D8_CLOSED:
        if "d8_closure_notes" in data:
            capa.d8_closure_notes = data["d8_closure_notes"]
        capa.status = CapaStatusChoices.CLOSED
        capa.closed_at = timezone.now()

    capa.current_discipline = target_discipline
    capa.save()
    return capa


@transaction.atomic
def record_voe_checkpoint(
    capa_id: uuid.UUID,
    milestone: str,
    defect_count: int,
    notes: str = "",
    verifier=None,
) -> CapaVoeRecord:
    """
    Submits evaluation for a 30, 60, or 90-day Verification of Effectiveness (VoE) milestone.
    If all three milestones pass with 0 defects, closes the 8D CAPA.
    """
    capa = Capa8dRecord.objects.select_for_update().get(id=capa_id)

    voe_record, _ = CapaVoeRecord.objects.get_or_create(
        capa=capa,
        milestone=milestone,
        defaults={
            "target_date": timezone.now().date(),
        },
    )

    is_effective = defect_count == 0
    voe_record.verified_date = timezone.now().date()
    voe_record.defect_count_in_period = defect_count
    voe_record.is_effective = is_effective
    voe_record.notes = notes
    if verifier:
        voe_record.verifier = verifier
    voe_record.save()

    # Check whether all 3 milestones are complete and effective
    all_checkpoints = list(capa.voe_checkpoints.all())
    completed_milestones = {
        cp.milestone for cp in all_checkpoints if cp.verified_date is not None and cp.is_effective
    }

    required_milestones = {
        VoeMilestoneChoices.DAY_30,
        VoeMilestoneChoices.DAY_60,
        VoeMilestoneChoices.DAY_90,
    }

    if required_milestones.issubset(completed_milestones):
        capa.current_discipline = CapaDisciplineChoices.D8_CLOSED
        capa.status = CapaStatusChoices.CLOSED
        if not capa.closed_at:
            capa.closed_at = timezone.now()
        capa.save()

    return voe_record
