from decimal import Decimal
from datetime import timedelta
import pytest
from django.urls import reverse
from django.utils import timezone
from apps.master_data.models import Part, ResinMaterial, PolymerTypeChoices
from apps.metrology.models.metrology import (
    Gauge,
    GaugeStatusChoices,
    GaugeTypeChoices,
    MsaStudy,
    MsaAcceptanceChoices,
)
from apps.metrology.services import (
    check_gauge_lockout,
    record_calibration,
    compute_anova_gauge_rr,
)


@pytest.fixture
def metro_part(db):
    material = ResinMaterial.objects.create(
        material_code="RES-METRO-01",
        material_name="Metrology Test Resin",
        polymer_type=PolymerTypeChoices.PA66,
        supplier_code="VEND-METRO",
        target_moisture_max_pct=Decimal("0.02"),
        target_mfi_nominal=Decimal("10.0"),
        target_mfi_tolerance=Decimal("1.0"),
    )
    part = Part.objects.create(
        part_number="PRD-METRO-001",
        part_name="Metrology Test Bracket",
        drawing_number="DWG-METRO-1",
        drawing_revision="A",
        material_code=material.material_code,
    )
    return part


@pytest.fixture
def active_gauge(db):
    today = timezone.now().date()
    gauge = Gauge.objects.create(
        device_id="GAGE-TST-001",
        name="Digital Caliper 150mm",
        gauge_type=GaugeTypeChoices.VERNIER_CALIPER,
        serial_number="CAL-SN-12345",
        location="QC Lab",
        resolution_mm=Decimal("0.0100"),
        calibration_interval_months=12,
        last_calibration_date=today - timedelta(days=30),
        next_calibration_due=today + timedelta(days=335),
        status=GaugeStatusChoices.ACTIVE,
    )
    return gauge


@pytest.fixture
def overdue_gauge(db):
    today = timezone.now().date()
    gauge = Gauge.objects.create(
        device_id="GAGE-OVERDUE-002",
        name="Height Gauge 300mm",
        gauge_type=GaugeTypeChoices.HEIGHT_GAUGE,
        serial_number="HGT-SN-9988",
        location="Cell 3",
        resolution_mm=Decimal("0.0100"),
        calibration_interval_months=12,
        last_calibration_date=today - timedelta(days=400),
        next_calibration_due=today - timedelta(days=35),
        status=GaugeStatusChoices.ACTIVE,
    )
    return gauge


@pytest.mark.django_db
class TestMetrologyGovernance:
    def test_check_gauge_lockout_active_gauge(self, active_gauge):
        locked_out, msg = check_gauge_lockout(active_gauge)
        assert locked_out is False

    def test_check_gauge_lockout_expired_calibration(self, overdue_gauge):
        locked_out, msg = check_gauge_lockout(overdue_gauge)
        assert locked_out is True
        overdue_gauge.refresh_from_db()
        assert overdue_gauge.status == GaugeStatusChoices.OVERDUE
        assert "Lockout" in msg

    def test_record_calibration_clears_lockout(self, overdue_gauge):
        today = timezone.now().date()
        cal = record_calibration(
            gauge=overdue_gauge,
            certificate_number="CERT-CAL-TEST-001",
            calibration_date=today,
            calibrated_by="ISO 17025 Certified Metrology Lab",
            next_due_date=today + timedelta(days=365),
            as_found_condition="OUT_OF_TOLERANCE",
            as_left_condition="IN_TOLERANCE",
            uncertainty_budget_mm=0.0015,
            notes="Adjusted zero offset and recalibrated.",
        )

        assert cal.id is not None
        overdue_gauge.refresh_from_db()
        assert overdue_gauge.status == GaugeStatusChoices.ACTIVE
        assert overdue_gauge.next_calibration_due == today + timedelta(days=365)

        # Verify lockout is cleared
        locked_out, _ = check_gauge_lockout(overdue_gauge)
        assert locked_out is False

    def test_compute_anova_gauge_rr_study(self, active_gauge, metro_part):
        # 10 parts x 3 operators x 3 trials with small variation
        raw_matrix = []
        base = 25.0
        for p in range(10):
            p_val = base + (p * 0.05)
            row = []
            for _ in range(3):
                trials = [round(p_val + 0.001, 3), round(p_val, 3), round(p_val - 0.001, 3)]
                row.append(trials)
            raw_matrix.append(row)

        study = MsaStudy.objects.create(
            study_number="MSA-TEST-001",
            gauge=active_gauge,
            part=metro_part,
            characteristic_name="Outer Diameter",
            tolerance=Decimal("0.5000"),
            part_count=10,
            operator_count=3,
            trial_count=3,
            raw_data=raw_matrix,
        )

        compute_anova_gauge_rr(study.id)
        study.refresh_from_db()

        assert study.repeatability_ev is not None
        assert study.reproducibility_av is not None
        assert study.grr is not None
        assert study.part_variation_pv is not None
        assert study.total_variation_tv is not None
        assert study.grr_percent is not None
        assert study.ndc is not None
        assert study.acceptance_status == MsaAcceptanceChoices.ACCEPTABLE


@pytest.mark.django_db
class TestMetrologyViews:
    def test_metrology_index_view(self, client, active_gauge):
        url = reverse("metrology:index")
        response = client.get(url)
        assert response.status_code == 200
        assert "Metrology &amp; Gauge Calibration" in response.content.decode()

    def test_record_calibration_post(self, client, overdue_gauge):
        today = timezone.now().date()
        url = reverse("metrology:record_calibration", kwargs={"gauge_id": overdue_gauge.id})
        data = {
            "certificate_number": "CAL-WEB-991",
            "calibrated_by": "Mitutoyo Lab",
            "calibration_date": today.strftime("%Y-%m-%d"),
            "next_calibration_due": (today + timedelta(days=365)).strftime("%Y-%m-%d"),
            "as_found_condition": "IN_TOLERANCE",
            "as_left_condition": "IN_TOLERANCE",
            "uncertainty_budget_mm": "0.0020",
        }
        response = client.post(url, data=data, follow=True)
        assert response.status_code == 200
        overdue_gauge.refresh_from_db()
        assert overdue_gauge.status == GaugeStatusChoices.ACTIVE

    def test_msa_study_detail_view(self, client, active_gauge, metro_part):
        study = MsaStudy.objects.create(
            study_number="MSA-VIEW-01",
            gauge=active_gauge,
            part=metro_part,
            characteristic_name="Height",
            tolerance=Decimal("0.2000"),
            raw_data=[[[10.0, 10.01], [10.0, 10.0]], [[10.5, 10.51], [10.5, 10.5]]],
        )
        url = reverse("metrology:msa_detail", kwargs={"study_id": study.id})
        response = client.get(url)
        assert response.status_code == 200
        assert study.study_number in response.content.decode()
