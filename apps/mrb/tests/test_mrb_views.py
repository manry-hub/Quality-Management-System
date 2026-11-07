import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from apps.ncr.models.ncr import (
    NonConformanceReport,
    SeverityLevel,
    SourceDomain,
    TargetType,
    DispositionType,
    NcrStatus,
)
from apps.mrb.models.mrb import MrbCase, MrbStatus, MrbRole, VoteChoice

User = get_user_model()


@pytest.fixture
def qa_user():
    return User.objects.create_user(
        username="qa_mrb_user",
        email="qa_mrb@example.com",
        badge_number="QA-MRB-001",
        department="Quality Assurance",
    )


@pytest.fixture
def sample_ncr():
    return NonConformanceReport.objects.create(
        source_domain=SourceDomain.IPQC,
        severity=SeverityLevel.MAJOR,
        target_type=TargetType.IN_PROCESS_RUN,
        target_identifier="IMM-01-RUN-440",
        defect_description="Sink mark depth exceeds 0.08mm limit",
        containment_actions="Machine paused, tooling inspected",
        hold_declared=True,
    )


@pytest.mark.django_db
class TestMrbViews:
    def test_mrb_index_renders_200(self, client):
        url = reverse("mrb:index")
        response = client.get(url)
        assert response.status_code == 200
        assert "Material Review Board" in response.content.decode()

    def test_mrb_initiate_post(self, client, qa_user, sample_ncr):
        client.force_login(qa_user)
        url = reverse("mrb:initiate")
        data = {
            "ncr_id": str(sample_ncr.id),
            "proposed_disposition": DispositionType.USE_AS_IS,
            "concession_rationale": "Non-visible ribbing surface, structural integrity intact.",
            "customer_doc": "DOC-OEM-APP-1234",
        }
        response = client.post(url, data)
        assert response.status_code == 302

        mrb_case = MrbCase.objects.filter(ncr=sample_ncr).first()
        assert mrb_case is not None
        assert mrb_case.proposed_disposition == DispositionType.USE_AS_IS
        assert mrb_case.status == MrbStatus.IN_DELIBERATION

    def test_mrb_vote_post(self, client, qa_user, sample_ncr):
        client.force_login(qa_user)
        mrb = MrbCase.objects.create(
            ncr=sample_ncr,
            chairperson=qa_user,
            proposed_disposition=DispositionType.REWORK,
            status=MrbStatus.IN_DELIBERATION,
        )

        url = reverse("mrb:vote", kwargs={"mrb_id": mrb.id})
        data = {
            "voter_role": MrbRole.OPERATIONS_LEAD,
            "vote": VoteChoice.APPROVE,
            "comments": "Rework SOP verified on 5 test samples.",
        }
        response = client.post(url, data)
        assert response.status_code == 302

        vote = mrb.votes.filter(voter_role=MrbRole.OPERATIONS_LEAD).first()
        assert vote is not None
        assert vote.vote == VoteChoice.APPROVE
        assert vote.signature_token is not None

    def test_mrb_finalize_post_enforces_four_eyes(self, client, qa_user, sample_ncr):
        client.force_login(qa_user)
        mrb = MrbCase.objects.create(
            ncr=sample_ncr,
            chairperson=qa_user,
            proposed_disposition=DispositionType.USE_AS_IS,
            status=MrbStatus.IN_DELIBERATION,
        )

        # Attempt to finalize USE_AS_IS without QM & Chief Engineer approval votes
        url = reverse("mrb:finalize", kwargs={"mrb_id": mrb.id})
        data = {
            "final_disposition": DispositionType.USE_AS_IS,
            "concession_rationale": "Minor deviation",
            "customer_doc": "DOC-OEM-123",
        }
        response = client.post(url, data)
        assert response.status_code == 302

        # Must NOT be approved due to Four-Eyes block
        mrb.refresh_from_db()
        assert mrb.status == MrbStatus.IN_DELIBERATION
        assert not mrb.final_disposition

    def test_mrb_finalize_post_succeeds_for_rework(self, client, qa_user, sample_ncr):
        client.force_login(qa_user)
        mrb = MrbCase.objects.create(
            ncr=sample_ncr,
            chairperson=qa_user,
            proposed_disposition=DispositionType.REWORK,
            status=MrbStatus.IN_DELIBERATION,
        )

        url = reverse("mrb:finalize", kwargs={"mrb_id": mrb.id})
        data = {
            "final_disposition": DispositionType.REWORK,
        }
        response = client.post(url, data)
        assert response.status_code == 302

        mrb.refresh_from_db()
        assert mrb.status == MrbStatus.APPROVED
        assert mrb.final_disposition == DispositionType.REWORK
        sample_ncr.refresh_from_db()
        assert sample_ncr.status == NcrStatus.DISPOSITIONED
