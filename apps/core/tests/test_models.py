import uuid
import pytest
from django.test import Client
from apps.core.models import User, OutboxEvent, OutboxStatusChoices, DepartmentChoices
from apps.master_data.models import Part, ResinMaterial
from apps.quality_planning.models import ControlPlan, ControlPlanItem


@pytest.mark.django_db
class TestCoreModels:
    def test_custom_user_creation(self):
        user = User.objects.create_user(
            username="metrologist_hilman",
            email="hilman@qms.plant",
            password="StrongPassword2026!",
            badge_number="BADGE-MET-771",
            department=DepartmentChoices.METROLOGY
        )
        assert str(user) == "metrologist_hilman (Metrology Lab)"
        assert user.badge_number == "BADGE-MET-771"
        assert user.department == DepartmentChoices.METROLOGY
        assert isinstance(user.id, uuid.UUID)

    def test_resin_material_creation(self):
        resin = ResinMaterial.objects.create(
            material_code="RES-PP-HOMO",
            material_name="Polypropylene Homopolymer",
            polymer_type="PP",
            supplier_code="VEND-LOTTE",
            target_moisture_max_pct=0.0200,
            target_mfi_nominal=12.000,
            target_mfi_tolerance=1.500
        )
        assert resin.material_code == "RES-PP-HOMO"
        assert resin.target_mfi_nominal == 12.000

    def test_outbox_event_lifecycle(self):
        outbox = OutboxEvent.objects.create(
            event_type="qms.quality_hold_declared",
            destination_system="WMS",
            payload={"lot_number": "LOT-PP-202610-01", "hold_reason": "High Moisture"}
        )
        assert outbox.status == OutboxStatusChoices.PENDING
        assert outbox.retry_count == 0
        assert outbox.event_uuid is not None

    def test_master_data_and_control_plan_relation(self):
        part = Part.objects.create(
            part_number="PRD-AUTO-BUMPER",
            part_name="Front Bumper Fascia",
            drawing_number="DWG-BUMP-2026",
            drawing_revision="REV-A",
            approved_mold_codes=["MOLD-BUMP-2C"],
            cavity_count=2,
            material_code="RES-PP-HOMO"
        )
        control_plan = ControlPlan.objects.create(
            part=part,
            revision="REV-A",
            status="DRAFT"
        )
        item = ControlPlanItem.objects.create(
            control_plan=control_plan,
            characteristic_name="Critical Bumper Width",
            characteristic_type="VARIABLE",
            target_value=1450.0000,
            usl=1452.0000,
            lsl=1448.0000,
            unit_of_measure="mm",
            tool_category="CMM"
        )
        assert control_plan.items.count() == 1
        assert item.target_value == 1450.0000


@pytest.mark.django_db
class TestHealthCheckView:
    def test_health_check_endpoint(self):
        client = Client()
        response = client.get("/health/")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        assert response.json()["service"] == "qms-automotive"
