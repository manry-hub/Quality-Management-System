import hashlib
import logging
from django.db import transaction
from django.utils import timezone
from apps.core.models.audit import AuditTrailEvent
from apps.core.models.outbox import OutboxEvent
from apps.ncr.models.ncr import NonConformanceReport, NcrStatus, DispositionType
from apps.mrb.models.mrb import MrbCase, MrbVote, MrbStatus, MrbRole, VoteChoice

logger = logging.getLogger(__name__)


@transaction.atomic
def create_mrb_case(
    ncr_id,
    chairperson,
    proposed_disposition: str = DispositionType.REWORK,
    concession_rationale: str = "",
    customer_doc: str = "",
) -> MrbCase:
    """
    Initializes an MRB deliberation case for a non-conformance.
    """
    ncr = NonConformanceReport.objects.select_for_update().get(id=ncr_id)
    if hasattr(ncr, "mrb_case"):
        return ncr.mrb_case

    customer_req = proposed_disposition == DispositionType.USE_AS_IS

    mrb_case = MrbCase.objects.create(
        ncr=ncr,
        chairperson=chairperson,
        proposed_disposition=proposed_disposition,
        concession_rationale=concession_rationale,
        customer_approval_doc=customer_doc,
        customer_approval_required=customer_req,
        status=MrbStatus.IN_DELIBERATION,
    )

    ncr.status = NcrStatus.IN_MRB_REVIEW
    ncr.save(update_fields=["status", "updated_at"])

    effective_badge = getattr(chairperson, "badge_number", "") or "QA-CHAIR"
    AuditTrailEvent.objects.create(
        action_type="MRB_CASE_INITIATED",
        entity_type="MrbCase",
        entity_id=mrb_case.id,
        badge_number=effective_badge,
        payload_snapshot={
            "mrb_id": str(mrb_case.id),
            "ncr_number": ncr.ncr_number,
            "proposed_disposition": proposed_disposition,
            "chairperson_badge": effective_badge,
        },
        signature_manifestation=f"MRB case initiated by {effective_badge} for {ncr.ncr_number}",
    )

    return mrb_case


@transaction.atomic
def submit_mrb_vote(
    mrb_case_id,
    voter,
    voter_role: str,
    vote: str,
    comments: str = "",
) -> MrbVote:
    """
    Records an MRB member vote accompanied by cryptographic SHA-256 signature manifestation.
    """
    mrb_case = MrbCase.objects.select_for_update().get(id=mrb_case_id)
    if mrb_case.status != MrbStatus.IN_DELIBERATION:
        raise ValueError(f"Cannot vote on MRB case in state '{mrb_case.status}'")

    effective_badge = getattr(voter, "badge_number", "") or f"VOTER-{voter.id}"
    timestamp_str = timezone.now().isoformat()
    raw_signature = f"{effective_badge}:{mrb_case_id}:{vote}:{voter_role}:{timestamp_str}"
    signature_token = hashlib.sha256(raw_signature.encode()).hexdigest()

    mrb_vote, created = MrbVote.objects.update_or_create(
        mrb_case=mrb_case,
        voter=voter,
        defaults={
            "voter_role": voter_role,
            "vote": vote,
            "comments": comments,
            "signature_token": signature_token,
        },
    )

    AuditTrailEvent.objects.create(
        action_type="MRB_VOTE_CAST",
        entity_type="MrbVote",
        entity_id=mrb_vote.id,
        badge_number=effective_badge,
        payload_snapshot={
            "mrb_case_id": str(mrb_case_id),
            "voter_badge": effective_badge,
            "voter_role": voter_role,
            "vote": vote,
            "signature_token": signature_token,
        },
        signature_manifestation=f"21 CFR Part 11 Vote cast by {effective_badge} ({voter_role}) as {vote}",
    )

    return mrb_vote


@transaction.atomic
def finalize_mrb_disposition(
    mrb_case_id,
    chairperson,
    final_disposition: str,
    concession_rationale: str = "",
    customer_doc: str = "",
) -> MrbCase:
    """
    Finalizes the MRB disposition.
    Enforces Four-Eyes Principle for Concessions (USE_AS_IS):
    Requires at least 2 APPROVE votes, including both Quality Manager and Chief Engineer,
    plus attached customer concession approval documentation.
    """
    mrb_case = MrbCase.objects.select_for_update().get(id=mrb_case_id)
    ncr = mrb_case.ncr

    # Enforce Four-Eyes Principle for Concession (USE_AS_IS)
    if final_disposition == DispositionType.USE_AS_IS:
        votes = mrb_case.votes.filter(vote=VoteChoice.APPROVE)
        roles = set(votes.values_list("voter_role", flat=True))

        has_qm = MrbRole.QUALITY_MANAGER in roles
        has_ce = MrbRole.CHIEF_ENGINEER in roles

        if not (has_qm and has_ce):
            raise ValueError(
                "Four-Eyes Principle breach: USE_AS_IS concession requires explicit approval from "
                "both Quality Manager and Chief Engineer."
            )

        effective_rationale = concession_rationale or mrb_case.concession_rationale
        effective_doc = customer_doc or mrb_case.customer_approval_doc

        if not effective_rationale:
            raise ValueError("USE_AS_IS concession mandates engineering rationale.")
        if not effective_doc:
            raise ValueError("USE_AS_IS concession mandates attached customer approval documentation.")

        mrb_case.concession_rationale = effective_rationale
        mrb_case.customer_approval_doc = effective_doc
        # Concession releases the quality hold
        ncr.hold_declared = False

    mrb_case.status = MrbStatus.APPROVED
    mrb_case.final_disposition = final_disposition
    mrb_case.closed_at = timezone.now()
    mrb_case.save()

    ncr.status = NcrStatus.DISPOSITIONED
    ncr.disposition_type = final_disposition
    ncr.save(update_fields=["status", "disposition_type", "hold_declared", "updated_at"])

    effective_badge = getattr(chairperson, "badge_number", "") or "QA-CHAIR"
    payload = {
        "mrb_case_id": str(mrb_case.id),
        "ncr_number": ncr.ncr_number,
        "final_disposition": final_disposition,
        "hold_declared": ncr.hold_declared,
        "closed_at": mrb_case.closed_at.isoformat(),
        "chairperson_badge": effective_badge,
    }

    OutboxEvent.objects.create(
        event_type="qms.mrb_dispositioned",
        destination_system="ALL",
        payload=payload,
    )

    AuditTrailEvent.objects.create(
        action_type="MRB_DISPOSITION_FINALIZED",
        entity_type="MrbCase",
        entity_id=mrb_case.id,
        badge_number=effective_badge,
        payload_snapshot=payload,
        signature_manifestation=f"MRB finalized as {final_disposition} by {effective_badge}",
    )

    return mrb_case
