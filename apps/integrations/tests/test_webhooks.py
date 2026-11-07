from decimal import Decimal
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from apps.master_data.models.material import ResinMaterial
from apps.master_data.models.part import Part
from apps.ipqc.models.ipqc_inspection import IpqcInspection, IpqcCavitySample


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def resin_pp(db):
    return ResinMaterial.objects.create(
        material_code="RES-PP-TD20",
        material_name="Sabic PP 20% Talc",
        polymer_type="PP",
        supplier_code="VEND-SABIC",
        target_moisture_max_pct=Decimal("0.0200"),
        target_mfi_nominal=Decimal("15.000"),
        target_mfi_tolerance=Decimal("2.000"),
    )


@pytest.fixture
def bumper_part(db):
    return Part.objects.create(
        part_number="PRD-AUTO-BUMPER-TEST",
        part_name="Front Bumper Fascia",
        drawing_number="DWG-BUMP-001",
        drawing_revision="REV-B",
        cavity_count=2,
        material_code="RES-PP-TD20",
    )


@pytest.mark.django_db
class TestIntegrationWebhooks:
    def test_wms_shipment_received_endpoint(self, api_client, resin_pp):
        url = reverse("integrations:wms_shipment_received")
        payload = {
            "wms_event_id": "WMS-RECEIVE-999",
            "material_code": "RES-PP-TD20",
            "lot_number": "LOT-PP-202611-99",
            "supplier_code": "VEND-SABIC",
            "quantity_kg": 3000.0,
            "pallet_barcodes": ["PAL-PP-01", "PAL-PP-02"],
        }
        response = api_client.post(url, data=payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["status"] == "SUCCESS"
        assert response.data["lot_number"] == "LOT-PP-202611-99"

    def test_mes_cycle_telemetry_endpoint(self, api_client):
        url = reverse("integrations:mes_cycle_telemetry")
        payload = {
            "machine_code": "IMM-04",
            "mold_code": "MOLD-BUMP-2C",
            "mes_run_id": "RUN-MES-404",
            "shot_number": 12,
            "cushion_mm": 5.15,
            "cushion_nominal_mm": 5.0,
            "peak_pressure_bar": 1180.0,
            "fill_time_s": 2.45,
            "cycle_time_s": 34.8,
        }
        response = api_client.post(url, data=payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["status"] == "INGESTED"
        assert response.data["cushion_drift_alert"] is False

    def test_ipqc_fai_approval_endpoint(self, api_client, bumper_part):
        inspection = IpqcInspection.objects.create(
            inspection_type="FIRST_PIECE_FAI",
            mes_run_id="MES-RUN-APPROVAL-01",
            machine_code="IMM-05",
            mold_code="MOLD-BUMP-2C",
            part=bumper_part,
            disposition="PENDING",
        )

        IpqcCavitySample.objects.create(
            inspection=inspection,
            cavity_number=1,
            shot_number=1,
            characteristic_name="Critical Width",
            measured_value=Decimal("1450.0000"),
            nominal_value=Decimal("1450.0000"),
            usl=Decimal("1452.0000"),
            lsl=Decimal("1448.0000"),
            is_conforming=True,
        )

        url = reverse("integrations:ipqc_fai_approval")
        response = api_client.post(
            url,
            data={"inspection_id": str(inspection.id), "badge_number": "BADGE-123"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "APPROVED"
        assert response.data["disposition"] == "RELEASED"
        assert "signature_token" in response.data
