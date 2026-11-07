import pytest
from django.core.management import call_command
from apps.master_data.models import Part, ResinMaterial
from apps.iqc.models.iqc_task import IqcInspectionTask
from apps.ipqc.models.ipqc_inspection import IpqcInspection
from apps.ipqc.models.telemetry import TelemetrySummary
from apps.oqc.models.oqc_inspection import OqcInspection
from apps.ncr.models.ncr import NonConformanceReport
from apps.mrb.models.mrb import MrbCase, MrbVote
from apps.traceability.models.traceability import TraceabilityNode


@pytest.mark.django_db
class TestSeedFactoryDemoCommand:
    def test_seed_factory_demo_populates_all_entities(self):
        call_command("seed_factory_demo", reset=True)

        # 1. Master Data
        assert ResinMaterial.objects.count() >= 4
        assert Part.objects.count() >= 4

        # 2. IQC
        assert IqcInspectionTask.objects.count() >= 5
        assert IqcInspectionTask.objects.filter(status="ACCEPTED").exists()
        assert IqcInspectionTask.objects.filter(status="REJECTED").exists()

        # 3. IPQC & Telemetry
        assert IpqcInspection.objects.count() >= 4
        assert TelemetrySummary.objects.count() >= 25
        assert TelemetrySummary.objects.filter(cushion_drift_alert=True).exists()

        # 4. OQC
        assert OqcInspection.objects.count() >= 4
        assert OqcInspection.objects.filter(status="RELEASED_FOR_SHIPMENT").exists()

        # 5. NCR & MRB
        assert NonConformanceReport.objects.count() >= 3
        assert NonConformanceReport.objects.filter(hold_declared=True).exists()
        assert MrbCase.objects.count() >= 1
        assert MrbVote.objects.count() >= 2

        # 6. Traceability Graph
        assert TraceabilityNode.objects.count() >= 8
        assert TraceabilityNode.objects.filter(node_identifier="SHIPMENT-SH-4491").exists()
        assert TraceabilityNode.objects.filter(node_identifier="RESIN-LOT-PA66-2026-081").exists()
