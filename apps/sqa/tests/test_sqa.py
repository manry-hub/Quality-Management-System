from decimal import Decimal
from datetime import timedelta
import pytest
from django.urls import reverse
from django.utils import timezone
from apps.master_data.models import ResinMaterial, PolymerTypeChoices
from apps.sqa.models.sqa import (
    Supplier,
    CertificateOfAnalysis,
    SupplierTierChoices,
    SupplierStatusChoices,
    ScorecardGradeChoices,
    CoaStatusChoices,
)
from apps.sqa.services import (
    validate_coa_data,
    ingest_supplier_coa,
    compute_supplier_scorecard,
)


@pytest.fixture
def sqa_material(db):
    return ResinMaterial.objects.create(
        material_code="MAT-SQA-PA66",
        material_name="SQA Test Polyamide 6.6",
        polymer_type=PolymerTypeChoices.PA66,
        supplier_code="SUP-TEST",
        target_moisture_max_pct=Decimal("0.0200"),
        target_mfi_nominal=Decimal("15.000"),
        target_mfi_tolerance=Decimal("2.000"),
    )


@pytest.fixture
def sqa_supplier(db):
    today = timezone.now().date()
    return Supplier.objects.create(
        code="SUP-TEST-01",
        name="Test Polymer Technologies",
        tier=SupplierTierChoices.TIER_1,
        status=SupplierStatusChoices.APPROVED,
        iso_certification="IATF 16949:2016 / ISO 9001",
        cert_expiry_date=today + timedelta(days=365),
        quality_contact_name="Quality Engineer",
        contact_email="qa@testpoly.com",
    )


@pytest.mark.django_db
def test_coa_validation_compliant(sqa_material):
    valid_params = {
        "moisture_pct": 0.015,
        "mfi_g_10min": 15.5,
        "density_g_cm3": 1.35,
    }
    is_compliant, score, deviations = validate_coa_data(sqa_material, valid_params)
    assert is_compliant is True
    assert score == 100.0
    assert len(deviations) == 0


@pytest.mark.django_db
def test_coa_validation_moisture_breach(sqa_material):
    breached_params = {
        "moisture_pct": 0.035,  # Max allowed is 0.0200
        "mfi_g_10min": 15.0,
    }
    is_compliant, score, deviations = validate_coa_data(sqa_material, breached_params)
    assert is_compliant is False
    assert score == 60.0
    assert any("Moisture content" in dev for dev in deviations)


@pytest.mark.django_db
def test_coa_validation_mfi_breach(sqa_material):
    breached_params = {
        "moisture_pct": 0.010,
        "mfi_g_10min": 19.5,  # Nominal 15 +/- 2 -> range [13, 17]
    }
    is_compliant, score, deviations = validate_coa_data(sqa_material, breached_params)
    assert is_compliant is False
    assert score == 60.0
    assert any("MFI" in dev for dev in deviations)


@pytest.mark.django_db
def test_coa_validation_multiple_breaches(sqa_material):
    breached_params = {
        "moisture_pct": 0.040,
        "mfi_g_10min": 25.0,
    }
    is_compliant, score, deviations = validate_coa_data(sqa_material, breached_params)
    assert is_compliant is False
    assert score == 20.0
    assert len(deviations) == 2


@pytest.mark.django_db
def test_ingest_supplier_coa_service(sqa_supplier, sqa_material):
    today = timezone.now().date()
    params = {
        "moisture_pct": 0.012,
        "mfi_g_10min": 14.8,
        "density_g_cm3": 1.36,
    }
    coa = ingest_supplier_coa(
        supplier=sqa_supplier,
        material=sqa_material,
        coa_number="COA-TEST-001",
        lot_number="LOT-TST-001",
        manufacture_date=today - timedelta(days=5),
        parameters=params,
    )
    assert coa.id is not None
    assert coa.status == CoaStatusChoices.APPROVED
    assert coa.compliance_score == Decimal("100.00")


@pytest.mark.django_db
def test_compute_supplier_scorecard(sqa_supplier, sqa_material):
    today = timezone.now().date()
    # Ingest 2 compliant CoAs
    ingest_supplier_coa(
        supplier=sqa_supplier,
        material=sqa_material,
        coa_number="COA-SC-001",
        lot_number="LOT-SC-001",
        manufacture_date=today - timedelta(days=10),
        parameters={"moisture_pct": 0.012, "mfi_g_10min": 15.0},
    )
    ingest_supplier_coa(
        supplier=sqa_supplier,
        material=sqa_material,
        coa_number="COA-SC-002",
        lot_number="LOT-SC-002",
        manufacture_date=today - timedelta(days=5),
        parameters={"moisture_pct": 0.014, "mfi_g_10min": 15.2},
    )
    scorecard = compute_supplier_scorecard(
        supplier=sqa_supplier,
        period_label="2026-Q1",
        on_time_delivery_pct=98.0,
    )
    assert scorecard.id is not None
    assert scorecard.ppm_defect_rate == Decimal("0.00")
    assert scorecard.grade == ScorecardGradeChoices.GRADE_A


@pytest.mark.django_db
def test_compute_supplier_scorecard_with_rejections(sqa_supplier, sqa_material):
    today = timezone.now().date()
    # Ingest 1 non-compliant CoA
    ingest_supplier_coa(
        supplier=sqa_supplier,
        material=sqa_material,
        coa_number="COA-REJ-001",
        lot_number="LOT-REJ-001",
        manufacture_date=today - timedelta(days=2),
        parameters={"moisture_pct": 0.045, "mfi_g_10min": 25.0},
    )
    scorecard = compute_supplier_scorecard(
        supplier=sqa_supplier,
        period_label="2026-Q1",
        on_time_delivery_pct=75.0,
    )
    assert scorecard.grade in [ScorecardGradeChoices.GRADE_C, ScorecardGradeChoices.GRADE_D]


@pytest.mark.django_db
def test_sqa_views(client, sqa_supplier, sqa_material):
    # 1. SQA Dashboard
    res = client.get(reverse("sqa:index"))
    assert res.status_code == 200
    assert "Supplier Quality Assurance" in res.content.decode()

    # 2. Supplier Detail
    res = client.get(reverse("sqa:supplier_detail", kwargs={"supplier_id": sqa_supplier.id}))
    assert res.status_code == 200
    assert sqa_supplier.name in res.content.decode()

    # 3. Ingest CoA POST
    post_data = {
        "coa_number": "COA-WEB-001",
        "supplier_id": str(sqa_supplier.id),
        "material_id": str(sqa_material.id),
        "lot_number": "LOT-WEB-999",
        "manufacture_date": "2026-03-01",
        "moisture_pct": "0.015",
        "mfi_g_10min": "15.0",
        "density_g_cm3": "1.35",
    }
    res = client.post(reverse("sqa:coa_validate"), post_data)
    assert res.status_code == 302
    assert CertificateOfAnalysis.objects.filter(coa_number="COA-WEB-001").exists()
