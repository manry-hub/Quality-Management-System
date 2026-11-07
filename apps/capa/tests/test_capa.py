import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.capa.models.capa import (
    Capa8dRecord,
    CapaDisciplineChoices,
    CapaStatusChoices,
    VoeMilestoneChoices,
)
from apps.capa.services import (
    create_8d_capa,
    advance_8d_discipline,
    record_voe_checkpoint,
)

User = get_user_model()


@pytest.fixture
def capa_users(db):
    champion = User.objects.create_user(
        username="capa_champion",
        email="champion@qms.local",
        password="ValidPassword123!",
        badge_number="QA-DIR-991",
        department="Executive QA",
    )
    leader = User.objects.create_user(
        username="capa_leader",
        email="leader@qms.local",
        password="ValidPassword123!",
        badge_number="ENG-882",
        department="Tooling",
    )
    return champion, leader


@pytest.mark.django_db
class TestCapa8dWorkflow:
    def test_create_8d_capa(self, capa_users):
        champion, leader = capa_users
        capa = create_8d_capa(
            title="Splay Marks on Door Armrest",
            champion=champion,
            leader=leader,
            d2_problem_statement="Who: Tech. What: Splay. Where: Armrest cavity 2. When: 10:00. How Many: 50 pcs.",
            team_members=[{"name": "Alice", "role": "Tooling"}],
        )

        assert capa.id is not None
        assert capa.capa_number.startswith("CAPA-")
        assert capa.current_discipline == CapaDisciplineChoices.D1_TEAM
        assert capa.status == CapaStatusChoices.OPEN
        assert len(capa.team_members) == 1

    def test_advance_disciplines_and_voe_instantiation(self, capa_users):
        champion, leader = capa_users
        capa = create_8d_capa(
            title="Short Shot in Radiator Grille",
            champion=champion,
            leader=leader,
            d2_problem_statement="Short shot occurring at end-of-fill ribs.",
        )

        # D3 Containment
        advance_8d_discipline(
            capa.id,
            CapaDisciplineChoices.D3_CONTAINMENT,
            {"d3_containment_action": "100% inspection gate and quarantine 200 boxes."},
        )
        capa.refresh_from_db()
        assert capa.current_discipline == CapaDisciplineChoices.D3_CONTAINMENT
        assert capa.status == CapaStatusChoices.IN_PROGRESS

        # D4 Root Cause with 5-Why and 6M
        advance_8d_discipline(
            capa.id,
            CapaDisciplineChoices.D4_ROOT_CAUSE,
            {
                "d4_root_cause_5why": [{"why": "Why short shot?", "answer": "Venting clogged."}],
                "d4_fishbone_data": {"machine": ["Vent depth 0.005mm instead of 0.025mm"]},
                "d4_root_cause_summary": "Inadequate mold cavity venting.",
            },
        )
        capa.refresh_from_db()
        assert capa.current_discipline == CapaDisciplineChoices.D4_ROOT_CAUSE
        assert len(capa.d4_root_cause_5why) == 1

        # D7 Prevention: automatically initiates 30, 60, 90-day VoE milestones
        advance_8d_discipline(
            capa.id,
            CapaDisciplineChoices.D7_PREVENTION,
            {
                "d7_preventive_actions": "Standardized ultrasonic vent cleaning PM.",
                "fmea_updated": True,
                "control_plan_updated": True,
            },
        )
        capa.refresh_from_db()
        assert capa.current_discipline == CapaDisciplineChoices.D7_PREVENTION
        assert capa.status == CapaStatusChoices.UNDER_VOE
        assert capa.voe_checkpoints.count() == 3

    def test_voe_milestone_completion_closes_capa(self, capa_users):
        champion, leader = capa_users
        capa = create_8d_capa(
            title="Weld Line Weakness on B-Pillar",
            champion=champion,
            leader=leader,
            d2_problem_statement="Weld line visible and fails 1500N tensile test.",
        )
        advance_8d_discipline(capa.id, CapaDisciplineChoices.D7_PREVENTION, {})

        # Complete 30-Day VoE
        record_voe_checkpoint(capa.id, VoeMilestoneChoices.DAY_30, defect_count=0, verifier=champion)
        capa.refresh_from_db()
        assert capa.status == CapaStatusChoices.UNDER_VOE

        # Complete 60-Day VoE
        record_voe_checkpoint(capa.id, VoeMilestoneChoices.DAY_60, defect_count=0, verifier=champion)
        capa.refresh_from_db()
        assert capa.status == CapaStatusChoices.UNDER_VOE

        # Complete 90-Day VoE -> Triggers D8 and CLOSED
        record_voe_checkpoint(capa.id, VoeMilestoneChoices.DAY_90, defect_count=0, verifier=champion)
        capa.refresh_from_db()
        assert capa.status == CapaStatusChoices.CLOSED
        assert capa.current_discipline == CapaDisciplineChoices.D8_CLOSED
        assert capa.closed_at is not None


@pytest.mark.django_db
class TestCapaViews:
    def test_capa_list_view(self, client, capa_users):
        champion, leader = capa_users
        create_8d_capa("Test CAPA", champion, leader, "Problem statement")
        url = reverse("capa:index")
        response = client.get(url)
        assert response.status_code == 200
        assert "8D Problem Solving" in response.content.decode()

    def test_capa_detail_view(self, client, capa_users):
        champion, leader = capa_users
        capa = create_8d_capa("Detail Test", champion, leader, "Problem statement")
        url = reverse("capa:detail", kwargs={"capa_id": capa.id})
        response = client.get(url)
        assert response.status_code == 200
        assert capa.capa_number in response.content.decode()

    def test_capa_create_post(self, client, capa_users):
        champion, leader = capa_users
        url = reverse("capa:create")
        data = {
            "title": "New Web Created CAPA",
            "d2_problem_statement": "Created via HTTP form post test",
            "champion_id": str(champion.id),
            "leader_id": str(leader.id),
        }
        response = client.post(url, data=data, follow=True)
        assert response.status_code == 200
        assert Capa8dRecord.objects.filter(title="New Web Created CAPA").exists()
