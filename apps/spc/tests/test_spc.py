from decimal import Decimal
import pytest
from django.urls import reverse
from apps.master_data.models import Part, ResinMaterial, PolymerTypeChoices
from apps.spc.models.spc import SpcControlChart
from apps.spc.services import (
    calculate_subgroup_metrics,
    evaluate_nelson_rules,
    record_spc_subgroup,
)


@pytest.fixture
def test_part(db):
    material = ResinMaterial.objects.create(
        material_code="RES-PP-T20-TEST",
        material_name="Test Polypropylene",
        polymer_type=PolymerTypeChoices.PP,
        supplier_code="VEND-TEST",
        target_moisture_max_pct=Decimal("0.02"),
        target_mfi_nominal=Decimal("12.5"),
        target_mfi_tolerance=Decimal("1.5"),
    )
    part = Part.objects.create(
        part_number="PRD-SPC-TEST-001",
        part_name="SPC Test Part",
        drawing_number="DWG-TEST",
        drawing_revision="A",
        material_code=material.material_code,
    )
    return part


@pytest.fixture
def spc_chart(db, test_part):
    chart = SpcControlChart.objects.create(
        part=test_part,
        characteristic_name="Flange Thickness",
        chart_type="XBAR_R",
        nominal=Decimal("10.0000"),
        usl=Decimal("10.3000"),
        lsl=Decimal("9.7000"),
        subgroup_size=5,
        unit_of_measure="mm",
        is_active=True,
    )
    return chart


@pytest.mark.django_db
class TestSpcStatisticalEngine:
    def test_calculate_subgroup_metrics(self):
        samples = [10.01, 10.03, 9.99, 10.00, 10.02]
        metrics = calculate_subgroup_metrics(samples)
        assert metrics["mean"] == 10.0100
        assert metrics["range"] == 0.0400
        assert metrics["std_dev"] > 0

    def test_evaluate_nelson_rule_1_beyond_3_sigma(self):
        # Center line = 10.0, sigma = 0.05. Point 10.20 is 4 sigma away.
        means = [10.0, 10.01, 10.20]
        violations = evaluate_nelson_rules(means, center_line=10.0, sigma=0.05)
        assert 1 in violations

    def test_evaluate_nelson_rule_2_nine_points_one_side(self):
        # 9 points strictly above center line
        means = [10.02] * 9
        violations = evaluate_nelson_rules(means, center_line=10.0, sigma=0.05)
        assert 2 in violations

    def test_evaluate_nelson_rule_3_six_points_trending(self):
        # 6 points strictly increasing
        means = [10.01, 10.02, 10.03, 10.04, 10.05, 10.06]
        violations = evaluate_nelson_rules(means, center_line=10.0, sigma=0.05)
        assert 3 in violations

    def test_evaluate_nelson_rule_4_fourteen_points_alternating(self):
        # 14 points alternating up and down
        means = [10.0, 10.05, 10.0, 10.05, 10.0, 10.05, 10.0, 10.05, 10.0, 10.05, 10.0, 10.05, 10.0, 10.05]
        violations = evaluate_nelson_rules(means, center_line=10.0, sigma=0.05)
        assert 4 in violations

    def test_evaluate_nelson_rule_5_two_of_three_beyond_2_sigma(self):
        # 2 out of 3 points beyond 2 sigma (2 * 0.05 = 0.10 => > 10.10)
        means = [10.12, 10.02, 10.14]
        violations = evaluate_nelson_rules(means, center_line=10.0, sigma=0.05)
        assert 5 in violations

    def test_evaluate_nelson_rule_6_four_of_five_beyond_1_sigma(self):
        # 4 out of 5 points beyond 1 sigma (> 10.05)
        means = [10.06, 10.07, 10.02, 10.08, 10.09]
        violations = evaluate_nelson_rules(means, center_line=10.0, sigma=0.05)
        assert 6 in violations

    def test_evaluate_nelson_rule_7_fifteen_points_in_zone_c(self):
        # 15 points all within 1 sigma (<= 0.05)
        means = [10.01] * 15
        violations = evaluate_nelson_rules(means, center_line=10.0, sigma=0.05)
        assert 7 in violations

    def test_evaluate_nelson_rule_8_eight_points_beyond_zone_c(self):
        # 8 points all beyond 1 sigma (> 0.05 from center)
        means = [10.08, 9.92, 10.07, 9.91, 10.09, 9.90, 10.08, 9.92]
        violations = evaluate_nelson_rules(means, center_line=10.0, sigma=0.05)
        assert 8 in violations

    def test_record_spc_subgroup_calculates_capability_and_limits(self, spc_chart):
        for _ in range(5):
            record_spc_subgroup(spc_chart.id, [10.01, 10.02, 9.99, 10.00, 10.01])

        spc_chart.refresh_from_db()
        assert spc_chart.center_line is not None
        assert spc_chart.ucl is not None
        assert spc_chart.lcl is not None
        assert spc_chart.cp is not None
        assert spc_chart.cpk is not None
        assert spc_chart.subgroups.count() == 5


@pytest.mark.django_db
class TestSpcViews:
    def test_spc_dashboard_view_renders_200(self, client, spc_chart):
        record_spc_subgroup(spc_chart.id, [10.01, 10.00, 10.02, 9.99, 10.01])
        url = reverse("spc:index")
        response = client.get(url)
        assert response.status_code == 200
        assert "Statistical Process Control" in response.content.decode()

    def test_spc_record_subgroup_post(self, client, spc_chart):
        url = reverse("spc:record_subgroup")
        data = {
            "chart_id": str(spc_chart.id),
            "sample_values": "10.02, 10.01, 9.99, 10.00, 10.03",
        }
        response = client.post(url, data=data, follow=True)
        assert response.status_code == 200
        assert spc_chart.subgroups.count() == 1
