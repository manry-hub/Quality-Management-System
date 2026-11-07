import pytest
from django.contrib.auth import get_user_model
from apps.core.models.audit import AuditTrailEvent
from apps.core.models.outbox import OutboxEvent

from apps.ncr.models.ncr import (
    NonConformanceReport,
    SourceDomain,
    SeverityLevel,
    NcrStatus,
    TargetType,
    DispositionType,
)
from apps.mrb.models.mrb import MrbStatus, MrbRole, VoteChoice
from apps.mrb.services import (
    create_mrb_case,
    submit_mrb_vote,
    finalize_mrb_disposition,
)

User = get_user_model()


@pytest.fixture
def quality_manager(db):
    return User.objects.create_user(
        username="quality_mgr",
        email="qm@qms.local",
        password="ValidPassword123!",
        badge_number="QA-MGR-001",
        department="QA",
    )


@pytest.fixture
def chief_engineer(db):
    return User.objects.create_user(
        username="chief_eng",
        email="ce@qms.local",
        password="ValidPassword123!",
        badge_number="ENG-CHIEF-001",
        department="Engineering",
    )


@pytest.fixture
def ops_lead(db):
    return User.objects.create_user(
        username="ops_lead",
        email="ops@qms.local",
        password="ValidPassword123!",
        badge_number="OPS-LEAD-001",
        department="Operations",
    )


@pytest.fixture
def sample_ncr(db, quality_manager):
    return NonConformanceReport.objects.create(
        source_domain=SourceDomain.IPQC,
        severity=SeverityLevel.MAJOR,
        target_type=TargetType.IN_PROCESS_RUN,
        target_identifier="IMM-04-RUN-2041",
        defect_description="Slight sink mark on non-visible ribbed boss (0.15mm depth)",
        containment_actions="Held 320 parts in quarantine zone",
        hold_declared=True,
        status=NcrStatus.OPEN_CONTAINED,
        created_by=quality_manager,
    )


@pytest.mark.django_db
class TestMrbWorkflowAndFourEyesPrinciple:
    def test_mrb_case_initiation(self, sample_ncr, quality_manager):
        mrb = create_mrb_case(
            ncr_id=sample_ncr.id,
            chairperson=quality_manager,
            proposed_disposition=DispositionType.USE_AS_IS,
            concession_rationale="Non-critical internal ribbing, does not compromise tensile strength.",
            customer_doc="CONCESSION-DOC-OEM-8891.pdf",
        )

        assert mrb.id is not None
        assert mrb.status == MrbStatus.IN_DELIBERATION
        assert mrb.customer_approval_required is True

        sample_ncr.refresh_from_db()
        assert sample_ncr.status == NcrStatus.IN_MRB_REVIEW

    def test_mrb_voting_records_digital_signature(self, sample_ncr, quality_manager, chief_engineer):
        mrb = create_mrb_case(
            ncr_id=sample_ncr.id,
            chairperson=quality_manager,
            proposed_disposition=DispositionType.REWORK,
        )

        vote = submit_mrb_vote(
            mrb_case_id=mrb.id,
            voter=chief_engineer,
            voter_role=MrbRole.CHIEF_ENGINEER,
            vote=VoteChoice.APPROVE,
            comments="Regrind acceptable up to 15% virgin blend.",
        )

        assert vote.id is not None
        assert vote.vote == VoteChoice.APPROVE
        assert len(vote.signature_token) == 64  # SHA-256 length

        audit = AuditTrailEvent.objects.filter(entity_id=vote.id).first()
        assert audit is not None
        assert audit.badge_number == "ENG-CHIEF-001"

    def test_four_eyes_principle_blocks_unauthorized_concession(
        self, sample_ncr, quality_manager, ops_lead
    ):
        mrb = create_mrb_case(
            ncr_id=sample_ncr.id,
            chairperson=quality_manager,
            proposed_disposition=DispositionType.USE_AS_IS,
        )

        # Only Operations Lead approves, Chief Engineer has NOT approved
        submit_mrb_vote(
            mrb_case_id=mrb.id,
            voter=quality_manager,
            voter_role=MrbRole.QUALITY_MANAGER,
            vote=VoteChoice.APPROVE,
            comments="Approved conditionally.",
        )
        submit_mrb_vote(
            mrb_case_id=mrb.id,
            voter=ops_lead,
            voter_role=MrbRole.OPERATIONS_LEAD,
            vote=VoteChoice.APPROVE,
            comments="Operations concurs.",
        )

        # Attempting USE_AS_IS without Chief Engineer must fail
        with pytest.raises(ValueError, match="Four-Eyes Principle breach"):
            finalize_mrb_disposition(
                mrb_case_id=mrb.id,
                chairperson=quality_manager,
                final_disposition=DispositionType.USE_AS_IS,
                concession_rationale="Sink marks within B-surface limits",
                customer_doc="OEM-CONCESSION-APPROVAL-2026.pdf",
            )

    def test_four_eyes_principle_successful_concession(
        self, sample_ncr, quality_manager, chief_engineer
    ):
        mrb = create_mrb_case(
            ncr_id=sample_ncr.id,
            chairperson=quality_manager,
            proposed_disposition=DispositionType.USE_AS_IS,
        )

        # Both QM and Chief Engineer vote APPROVE
        submit_mrb_vote(
            mrb_case_id=mrb.id,
            voter=quality_manager,
            voter_role=MrbRole.QUALITY_MANAGER,
            vote=VoteChoice.APPROVE,
            comments="Approved by Quality.",
        )
        submit_mrb_vote(
            mrb_case_id=mrb.id,
            voter=chief_engineer,
            voter_role=MrbRole.CHIEF_ENGINEER,
            vote=VoteChoice.APPROVE,
            comments="Approved by Chief Engineer.",
        )

        finalized_mrb = finalize_mrb_disposition(
            mrb_case_id=mrb.id,
            chairperson=quality_manager,
            final_disposition=DispositionType.USE_AS_IS,
            concession_rationale="Ribbing sink depth 0.12mm verified non-functional.",
            customer_doc="OEM-CONCESSION-DOC-8891.pdf",
        )

        assert finalized_mrb.status == MrbStatus.APPROVED
        assert finalized_mrb.final_disposition == DispositionType.USE_AS_IS

        sample_ncr.refresh_from_db()
        assert sample_ncr.status == NcrStatus.DISPOSITIONED
        assert sample_ncr.hold_declared is False  # Concession releases hold

        # Outbox event
        outbox = OutboxEvent.objects.filter(
            event_type="qms.mrb_dispositioned",
        ).first()
        assert outbox is not None
        assert outbox.payload["mrb_case_id"] == str(finalized_mrb.id)
        assert outbox is not None
        assert outbox.payload["final_disposition"] == "USE_AS_IS"
        assert outbox.payload["hold_declared"] is False
