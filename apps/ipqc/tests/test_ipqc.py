from decimal import Decimal
import time
import pytest
from django.contrib.auth import get_user_model
from apps.core.models.outbox import OutboxEvent
from apps.master_data.models.part import Part
from apps.ipqc.models.ipqc_inspection import IpqcInspection, IpqcCavitySample
from apps.ipqc.services import evaluate_and_release_fai, process_cycle_telemetry

User = get_user_model()


@pytest.fixture
def sample_part(db):
    return Part.objects.create(
        part_number="PRD-AUTO-BUMPER",
        part_name="Front Bumper Fascia",
        drawing_number="DWG-BUMP-001",
        drawing_revision="REV-C",
        cavity_count=2,
        material_code="RES-PP-TD20",
    )


@pytest.fixture
def inspector_user(db):
    return User.objects.create_user(
        username="ipqc_inspector_1",
        email="ipqc1@qms.local",
        password="ValidPassword123!",
        badge_number="QA-IPQC-002",
        department="QC",
    )


@pytest.mark.django_db
class TestIpqcOperations:
    def test_fai_approval_issues_cryptographic_token_sub_200ms(
        self, sample_part, inspector_user
    ):
        inspection = IpqcInspection.objects.create(
            inspection_type="FIRST_PIECE_FAI",
            mes_run_id="MES-RUN-20261107-01",
            machine_code="IMM-01",
            mold_code="MOLD-BUMP-2C",
            part=sample_part,
            disposition="PENDING",
        )

        # Create 2 cavity conforming samples
        for cav in [1, 2]:
            IpqcCavitySample.objects.create(
                inspection=inspection,
                cavity_number=cav,
                shot_number=1,
                characteristic_name="Critical Bumper Width",
                measured_value=Decimal("1450.2000"),
                nominal_value=Decimal("1450.0000"),
                usl=Decimal("1452.0000"),
                lsl=Decimal("1448.0000"),
                is_conforming=True,
            )

        start_time = time.perf_counter()
        approved, token, message = evaluate_and_release_fai(inspection, inspector_user)
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        assert approved is True
        assert len(token) == 64  # HMAC-SHA256 hex string
        assert inspection.disposition == "RELEASED"
        assert inspection.signature_token == token
        assert elapsed_ms < 200.0, f"FAI approval took {elapsed_ms:.2f}ms (must be < 200ms)"

        # Check Outbox event emitted for MES
        event = OutboxEvent.objects.filter(
            event_type="qms.fai_released",
            destination_system="MES",
        ).first()
        assert event is not None
        assert event.payload["mes_run_id"] == "MES-RUN-20261107-01"
        assert event.payload["signature_token"] == token
        assert event.payload["status"] == "APPROVED"

    def test_fai_rejection_on_nonconforming_sample(
        self, sample_part, inspector_user
    ):
        inspection = IpqcInspection.objects.create(
            inspection_type="FIRST_PIECE_FAI",
            mes_run_id="MES-RUN-20261107-02",
            machine_code="IMM-02",
            mold_code="MOLD-BUMP-2C",
            part=sample_part,
            disposition="PENDING",
        )

        IpqcCavitySample.objects.create(
            inspection=inspection,
            cavity_number=1,
            shot_number=1,
            characteristic_name="Critical Bumper Width",
            measured_value=Decimal("1453.5000"),  # > USL 1452.0000
            nominal_value=Decimal("1450.0000"),
            usl=Decimal("1452.0000"),
            lsl=Decimal("1448.0000"),
            is_conforming=False,
        )

        approved, token, message = evaluate_and_release_fai(inspection, inspector_user)

        assert approved is False
        assert token == ""
        assert inspection.disposition == "REJECTED"
        assert inspection.line_stop_triggered is True

        event = OutboxEvent.objects.filter(
            event_type="qms.fai_rejected",
            destination_system="MES",
        ).first()
        assert event is not None
        assert event.payload["status"] == "REJECTED"

    def test_telemetry_cushion_drift_andon_trigger(self):
        machine = "IMM-03"
        run_id = "MES-RUN-TELEM-01"

        # Ingest 2 shots with drift: should alert individually but not trigger line stop
        for shot in [1, 2]:
            s = process_cycle_telemetry(
                {
                    "machine_code": machine,
                    "mold_code": "MOLD-BUMP-2C",
                    "mes_run_id": run_id,
                    "shot_number": shot,
                    "cushion_mm": 5.80,  # nominal is 5.0, delta is 0.8 > 0.5
                    "cushion_nominal_mm": 5.00,
                    "peak_pressure_bar": 1250.0,
                    "fill_time_s": 2.6,
                    "cycle_time_s": 35.0,
                }
            )
            assert s.cushion_drift_alert is True

        # Ensure no line stop event yet
        assert OutboxEvent.objects.filter(event_type="qms.andon_line_stop").count() == 0

        # Ingest 3rd consecutive drifting shot: must trigger Andon line stop
        s3 = process_cycle_telemetry(
            {
                "machine_code": machine,
                "mold_code": "MOLD-BUMP-2C",
                "mes_run_id": run_id,
                "shot_number": 3,
                "cushion_mm": 5.85,
                "cushion_nominal_mm": 5.00,
                "peak_pressure_bar": 1260.0,
                "fill_time_s": 2.6,
                "cycle_time_s": 35.0,
            }
        )
        assert s3.cushion_drift_alert is True

        event = OutboxEvent.objects.filter(
            event_type="qms.andon_line_stop",
            destination_system="MES",
        ).first()
        assert event is not None
        assert event.payload["machine_code"] == machine
        assert "cushion deviated" in event.payload["reason"]
