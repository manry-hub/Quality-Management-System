import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from apps.ncr.models.ncr import NonConformanceReport, SeverityLevel, SourceDomain, TargetType, NcrStatus

User = get_user_model()


@pytest.fixture
def qa_user():
    return User.objects.create_user(
        username="qa_view_user",
        email="qa_view@example.com",
        badge_number="QA-VIEW-001",
        department="Quality Assurance",
    )


@pytest.mark.django_db
class TestNcrViews:
    def test_ncr_index_renders_200(self, client):
        url = reverse("ncr:index")
        response = client.get(url)
        assert response.status_code == 200
        assert "Non-Conformance" in response.content.decode()

    def test_ncr_declare_hold_post(self, client, qa_user):
        client.force_login(qa_user)
        url = reverse("ncr:declare_hold")
        data = {
            "source_domain": SourceDomain.IPQC,
            "severity": SeverityLevel.CRITICAL,
            "target_type": TargetType.IN_PROCESS_RUN,
            "target_identifier": "IMM-03-RUN-999",
            "defect_description": "Excess flash on cavity 1 causing dimensional out-of-spec",
            "containment_actions": "Quarantine cage lock engaged, IMM-03 paused",
            "badge_number": "QA-TEST-001",
        }
        response = client.post(url, data)
        assert response.status_code == 302
        assert response.url == reverse("ncr:index")

        ncr = NonConformanceReport.objects.filter(target_identifier="IMM-03-RUN-999").first()
        assert ncr is not None
        assert ncr.severity == SeverityLevel.CRITICAL
        assert ncr.hold_declared is True
        assert ncr.status == NcrStatus.OPEN_CONTAINED

    def test_ncr_close_post(self, client, qa_user):
        client.force_login(qa_user)
        ncr = NonConformanceReport.objects.create(
            source_domain=SourceDomain.OQC,
            severity=SeverityLevel.MINOR,
            target_type=TargetType.FINISHED_GOODS,
            target_identifier="PL-9912",
            defect_description="Scuffed barcode label",
            containment_actions="Reprinted label",
            hold_declared=False,
            status=NcrStatus.OPEN_CONTAINED,
        )

        url = reverse("ncr:close", kwargs={"ncr_id": ncr.id})
        data = {
            "resolution_notes": "Labels verified with scanner, 100% readability confirmed.",
            "badge_number": "QA-MGR-002",
        }
        response = client.post(url, data)
        assert response.status_code == 302

        ncr.refresh_from_db()
        assert ncr.status == NcrStatus.CLOSED
        assert "Labels verified" in ncr.containment_actions
