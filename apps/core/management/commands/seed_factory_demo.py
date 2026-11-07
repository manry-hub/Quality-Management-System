from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.master_data.models import Part, ResinMaterial, PolymerTypeChoices
from apps.quality_planning.models import ControlPlan
from apps.iqc.models.iqc_task import IqcInspectionTask
from apps.ipqc.models.ipqc_inspection import IpqcInspection
from apps.ipqc.models.telemetry import TelemetrySummary
from apps.oqc.models.oqc_inspection import OqcInspection
from apps.ncr.models.ncr import (
    NonConformanceReport,
    SourceDomain,
    SeverityLevel,
    TargetType,
    NcrStatus,
    DispositionType,
)
from apps.mrb.models.mrb import MrbCase, MrbVote, MrbStatus, MrbRole, VoteChoice
from apps.traceability.models.traceability import TraceabilityNode, NodeType
from apps.core.models.audit import AuditTrailEvent

User = get_user_model()


class Command(BaseCommand):
    help = (
        "Seeds comprehensive, realistic automotive injection molding plant operational data across all QMS terminals."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Purge existing operational transactions before seeding",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("🚀 Starting Enterprise QMS Factory Demo Data Seeding..."))

        if options.get("reset"):
            self.stdout.write("Purging operational records...")
            MrbVote.objects.all().delete()
            MrbCase.objects.all().delete()
            NonConformanceReport.objects.all().delete()
            TraceabilityNode.objects.all().delete()
            OqcInspection.objects.all().delete()
            TelemetrySummary.objects.all().delete()
            IpqcInspection.objects.all().delete()
            IqcInspectionTask.objects.all().delete()
            self.stdout.write(self.style.WARNING("Existing operational data cleared."))

        # ---------------------------------------------------------------------
        # 1. PLANT USERS & PERSONAS
        # ---------------------------------------------------------------------
        self.stdout.write("1. Creating plant personas & IATF 16949 badge signers...")
        users_config = [
            {
                "username": "admin",
                "email": "director@qms.local",
                "first_name": "Alexander",
                "last_name": "Vance",
                "badge_number": "QA-DIR-001",
                "department": "Executive Quality",
                "is_staff": True,
                "is_superuser": True,
                "password": "AdminPass123!",
            },
            {
                "username": "qa_manager",
                "email": "qa.manager@qms.local",
                "first_name": "Sarah",
                "last_name": "Lin",
                "badge_number": "QA-MGR-001",
                "department": "Quality Assurance",
                "is_staff": True,
                "is_superuser": False,
                "password": "ManagerPass123!",
            },
            {
                "username": "chief_engineer",
                "email": "chief.eng@qms.local",
                "first_name": "Marcus",
                "last_name": "Weber",
                "badge_number": "ENG-CHIEF-001",
                "department": "Manufacturing Engineering",
                "is_staff": True,
                "is_superuser": False,
                "password": "EngineerPass123!",
            },
            {
                "username": "qc_inspector",
                "email": "inspector@qms.local",
                "first_name": "Elena",
                "last_name": "Rostova",
                "badge_number": "QC-INSP-001",
                "department": "Quality Control",
                "is_staff": False,
                "is_superuser": False,
                "password": "InspectorPass123!",
            },
            {
                "username": "ops_lead",
                "email": "ops.lead@qms.local",
                "first_name": "Devon",
                "last_name": "Kowalski",
                "badge_number": "OPS-LEAD-001",
                "department": "Plant Operations",
                "is_staff": False,
                "is_superuser": False,
                "password": "OperatorPass123!",
            },
        ]

        user_map = {}
        for uc in users_config:
            pwd = uc.pop("password")
            user, created = User.objects.update_or_create(username=uc["username"], defaults=uc)
            user.set_password(pwd)
            user.save()
            user_map[uc["username"]] = user

        self.stdout.write(self.style.SUCCESS(f"  Initialized {len(user_map)} personas."))

        # ---------------------------------------------------------------------
        # 2. MASTER DATA: POLYMER MATERIALS & AUTOMOTIVE PARTS
        # ---------------------------------------------------------------------
        self.stdout.write("2. Seeding engineering polymer materials & automotive parts...")
        materials_data = [
            {
                "material_code": "RES-PA66-GF30",
                "material_name": "Polyamide 6.6 30% Glass Fiber Reinforced",
                "polymer_type": PolymerTypeChoices.PA66,
                "supplier_code": "VEND-DUPONT",
                "target_moisture_max_pct": Decimal("0.0150"),
                "target_mfi_nominal": Decimal("15.000"),
                "target_mfi_tolerance": Decimal("2.000"),
            },
            {
                "material_code": "RES-PP-T20",
                "material_name": "Polypropylene 20% Mineral Talc Filled",
                "polymer_type": PolymerTypeChoices.PP,
                "supplier_code": "VEND-LYONDELL",
                "target_moisture_max_pct": Decimal("0.0200"),
                "target_mfi_nominal": Decimal("12.500"),
                "target_mfi_tolerance": Decimal("1.500"),
            },
            {
                "material_code": "RES-ABS-PC",
                "material_name": "Polycarbonate / ABS High Heat Impact Blend",
                "polymer_type": PolymerTypeChoices.ABS,
                "supplier_code": "VEND-COVESTRO",
                "target_moisture_max_pct": Decimal("0.0200"),
                "target_mfi_nominal": Decimal("18.000"),
                "target_mfi_tolerance": Decimal("2.000"),
            },
            {
                "material_code": "RES-POM-CO",
                "material_name": "Polyoxymethylene Copolymer (High Wear)",
                "polymer_type": PolymerTypeChoices.POM,
                "supplier_code": "VEND-CELANESE",
                "target_moisture_max_pct": Decimal("0.0100"),
                "target_mfi_nominal": Decimal("9.000"),
                "target_mfi_tolerance": Decimal("1.000"),
            },
        ]
        material_map = {}
        for m in materials_data:
            mat, _ = ResinMaterial.objects.update_or_create(material_code=m["material_code"], defaults=m)
            material_map[m["material_code"]] = mat

        parts_data = [
            {
                "part_number": "PRD-FASCIA-FR",
                "part_name": "Front Bumper Fascia (Aerodynamic Lower)",
                "drawing_number": "DWG-BUMP-2026-X1",
                "drawing_revision": "REV-C",
                "approved_mold_codes": ["MOLD-BUMP-2C"],
                "cavity_count": 2,
                "material_code": "RES-PP-T20",
            },
            {
                "part_number": "PRD-IP-BEZEL",
                "part_name": "Cockpit Instrument Panel Center Bezel",
                "drawing_number": "DWG-BEZEL-2026-R4",
                "drawing_revision": "REV-D",
                "approved_mold_codes": ["MOLD-BEZEL-4C"],
                "cavity_count": 4,
                "material_code": "RES-ABS-PC",
            },
            {
                "part_number": "PRD-DOOR-TRIM",
                "part_name": "Interior Door Handle Reinforcement Bracket",
                "drawing_number": "DWG-DOOR-2026-B1",
                "drawing_revision": "REV-A",
                "approved_mold_codes": ["MOLD-TRIM-4C"],
                "cavity_count": 4,
                "material_code": "RES-PA66-GF30",
            },
            {
                "part_number": "PRD-GEAR-ACT",
                "part_name": "HVAC Air Distribution Flap Actuator Pinion",
                "drawing_number": "DWG-GEAR-2026-P8",
                "drawing_revision": "REV-E",
                "approved_mold_codes": ["MOLD-GEAR-8C"],
                "cavity_count": 8,
                "material_code": "RES-POM-CO",
            },
        ]
        part_map = {}
        for p in parts_data:
            part, _ = Part.objects.update_or_create(part_number=p["part_number"], defaults=p)
            part_map[p["part_number"]] = part

            # Control plan
            ControlPlan.objects.get_or_create(
                part=part,
                revision="REV-01",
                defaults={
                    "status": "APPROVED",
                    "fmea_reference": f"PFMEA-2026-{part.part_number}",
                    "approved_by": user_map["qa_manager"],
                },
            )

        self.stdout.write(self.style.SUCCESS(f"  Initialized {len(parts_data)} parts and control plans."))

        # ---------------------------------------------------------------------
        # 3. IQC RECEIVING DOCK QUEUE & LABORATORY CLEARANCES
        # ---------------------------------------------------------------------
        self.stdout.write("3. Seeding IQC incoming polymer receiving shipments...")
        iqc_tasks = [
            {
                "wms_event_id": "WMS-RCV-2026-001",
                "lot_number": "LOT-PA66-2026-081",
                "material": material_map["RES-PA66-GF30"],
                "supplier_code": "VEND-DUPONT",
                "quantity_kg": Decimal("5000.00"),
                "status": "ACCEPTED",
                "disposition": "RELEASE_TO_AVAILABLE",
                "coa_moisture_pct": Decimal("0.0100"),
                "coa_mfi_value": Decimal("15.100"),
                "physical_moisture_pct": Decimal("0.0112"),
                "physical_mfi_value": Decimal("15.200"),
            },
            {
                "wms_event_id": "WMS-RCV-2026-002",
                "lot_number": "LOT-PP-2026-104",
                "material": material_map["RES-PP-T20"],
                "supplier_code": "VEND-LYONDELL",
                "quantity_kg": Decimal("8000.00"),
                "status": "ACCEPTED",
                "disposition": "RELEASE_TO_AVAILABLE",
                "coa_moisture_pct": Decimal("0.0150"),
                "coa_mfi_value": Decimal("12.200"),
                "physical_moisture_pct": Decimal("0.0165"),
                "physical_mfi_value": Decimal("12.100"),
            },
            {
                "wms_event_id": "WMS-RCV-2026-003",
                "lot_number": "LOT-ABS-2026-210",
                "material": material_map["RES-ABS-PC"],
                "supplier_code": "VEND-COVESTRO",
                "quantity_kg": Decimal("4500.00"),
                "status": "PENDING_INSPECTION",
                "disposition": "NONE",
                "coa_moisture_pct": Decimal("0.0180"),
                "coa_mfi_value": Decimal("17.900"),
            },
            {
                "wms_event_id": "WMS-RCV-2026-004",
                "lot_number": "LOT-POM-2026-044",
                "material": material_map["RES-POM-CO"],
                "supplier_code": "VEND-CELANESE",
                "quantity_kg": Decimal("3000.00"),
                "status": "PENDING_INSPECTION",
                "disposition": "NONE",
            },
            {
                "wms_event_id": "WMS-RCV-2026-005",
                "lot_number": "LOT-PP-2026-099",
                "material": material_map["RES-PP-T20"],
                "supplier_code": "VEND-LYONDELL",
                "quantity_kg": Decimal("6000.00"),
                "status": "REJECTED",
                "disposition": "QUARANTINE_REJECTED",
                "coa_moisture_pct": Decimal("0.0190"),
                "coa_mfi_value": Decimal("12.000"),
                "physical_moisture_pct": Decimal("0.0385"),  # Out of spec!
                "physical_mfi_value": Decimal("12.050"),
                "rejection_reason": "Severe moisture absorption (0.0385% > 0.0200% max). High splay risk.",
            },
        ]
        for it in iqc_tasks:
            IqcInspectionTask.objects.update_or_create(lot_number=it["lot_number"], defaults=it)

        self.stdout.write(self.style.SUCCESS(f"  Initialized {len(iqc_tasks)} IQC receiving records."))

        # ---------------------------------------------------------------------
        # 4. IPQC FIRST-ARTICLE INSPECTIONS & LIVE SPC TELEMETRY SHOTS
        # ---------------------------------------------------------------------
        self.stdout.write("4. Seeding IPQC First-Article Inspections & injection telemetry shots...")
        ipqc_configs = [
            {
                "mes_run_id": "IMM-01-RUN-882",
                "machine_code": "IMM-01",
                "mold_code": "MOLD-TRIM-4C",
                "part": part_map["PRD-DOOR-TRIM"],
                "disposition": "RELEASED",
                "signature_token": "SHA256:FAI-IMM-01-APPROVED-001",
            },
            {
                "mes_run_id": "IMM-02-RUN-883",
                "machine_code": "IMM-02",
                "mold_code": "MOLD-BEZEL-4C",
                "part": part_map["PRD-IP-BEZEL"],
                "disposition": "RELEASED",
                "signature_token": "SHA256:FAI-IMM-02-APPROVED-002",
            },
            {
                "mes_run_id": "IMM-03-RUN-884",
                "machine_code": "IMM-03",
                "mold_code": "MOLD-BUMP-2C",
                "part": part_map["PRD-FASCIA-FR"],
                "disposition": "REJECTED",
                "signature_token": "",
            },
            {
                "mes_run_id": "IMM-04-RUN-885",
                "machine_code": "IMM-04",
                "mold_code": "MOLD-GEAR-8C",
                "part": part_map["PRD-GEAR-ACT"],
                "disposition": "PENDING",
                "signature_token": "",
            },
        ]
        for ipc in ipqc_configs:
            IpqcInspection.objects.update_or_create(mes_run_id=ipc["mes_run_id"], defaults=ipc)

        # 25 Consecutive Telemetry shots for Machine IMM-02 (Screw Cushion SPC Series)
        # Baseline around 5.02mm, drifting upwards to 5.62mm at the end
        cushion_drift_values = [
            5.02, 5.01, 5.04, 4.99, 5.03,
            5.02, 5.05, 5.00, 5.02, 5.03,
            5.04, 5.02, 5.06, 5.08, 5.12,
            5.15, 5.18, 5.22, 5.28, 5.34,
            5.38, 5.44, 5.49, 5.54, 5.62,
        ]
        for idx, cushion_val in enumerate(cushion_drift_values, start=1):
            is_alert = cushion_val > 5.500 or cushion_val < 4.500
            TelemetrySummary.objects.create(
                machine_code="IMM-02",
                mold_code="MOLD-BEZEL-4C",
                mes_run_id="IMM-02-RUN-883",
                shot_number=idx,
                cushion_mm=Decimal(str(cushion_val)),
                peak_pressure_bar=Decimal("142.50") + Decimal(str(idx * 0.4)),
                fill_time_s=Decimal("2.450"),
                cycle_time_s=Decimal("28.40"),
                cushion_nominal_mm=Decimal("5.000"),
                cushion_drift_alert=is_alert,
            )

        self.stdout.write(
            self.style.SUCCESS("  Initialized IPQC inspections and 25 SPC shots with induced cushion drift.")
        )

        # ---------------------------------------------------------------------
        # 5. OQC OUTGOING QUALITY INSPECTIONS (c=0 ISO 2859-1)
        # ---------------------------------------------------------------------
        self.stdout.write("5. Seeding OQC finished goods sampling terminal records...")
        oqc_records = [
            {
                "pallet_barcode": "PALLET-PL-9021",
                "part": part_map["PRD-DOOR-TRIM"],
                "batch_quantity": 1000,
                "sample_size": 80,
                "defects_found": 0,
                "packaging_box_intact": True,
                "esd_bag_sealed": True,
                "desiccant_present": True,
                "datamatrix_verified": True,
                "coc_number": "COC-2026-0001",
                "status": "RELEASED_FOR_SHIPMENT",
            },
            {
                "pallet_barcode": "PALLET-PL-9022",
                "part": part_map["PRD-IP-BEZEL"],
                "batch_quantity": 800,
                "sample_size": 80,
                "defects_found": 0,
                "packaging_box_intact": True,
                "esd_bag_sealed": True,
                "desiccant_present": True,
                "datamatrix_verified": True,
                "coc_number": "COC-2026-0002",
                "status": "RELEASED_FOR_SHIPMENT",
            },
            {
                "pallet_barcode": "PALLET-PL-9023",
                "part": part_map["PRD-FASCIA-FR"],
                "batch_quantity": 500,
                "sample_size": 50,
                "defects_found": 0,
                "status": "PENDING",
            },
            {
                "pallet_barcode": "PALLET-PL-9024",
                "part": part_map["PRD-GEAR-ACT"],
                "batch_quantity": 2000,
                "sample_size": 125,
                "defects_found": 2,  # Breaches c=0!
                "packaging_box_intact": True,
                "esd_bag_sealed": True,
                "status": "REJECTED",
            },
        ]
        for oqc in oqc_records:
            OqcInspection.objects.update_or_create(pallet_barcode=oqc["pallet_barcode"], defaults=oqc)

        self.stdout.write(self.style.SUCCESS(f"  Initialized {len(oqc_records)} OQC shipment lots."))

        # ---------------------------------------------------------------------
        # 6. NON-CONFORMANCE REPORTS (NCR) & ACTIVE QUALITY HOLDS
        # ---------------------------------------------------------------------
        self.stdout.write("6. Seeding NCR ledger & multi-system quarantine holds...")
        ncrs_config = [
            {
                "source_domain": SourceDomain.IPQC,
                "severity": SeverityLevel.CRITICAL,
                "target_type": TargetType.IN_PROCESS_RUN,
                "target_identifier": "IMM-03-RUN-884",
                "defect_description": (
                    "Screw cushion runaway at shot #45 resulted in heavy parting line flash on cavity 1."
                ),
                "containment_actions": (
                    "IMM-03 injection press locked out via MES. Hopper gate closed. 80 molded parts quarantined."
                ),
                "hold_declared": True,
                "status": NcrStatus.IN_MRB_REVIEW,
                "created_by": user_map["qa_manager"],
            },
            {
                "source_domain": SourceDomain.IQC,
                "severity": SeverityLevel.MAJOR,
                "target_type": TargetType.MATERIAL_LOT,
                "target_identifier": "LOT-PP-2026-099",
                "defect_description": (
                    "Tested moisture 0.0385% significantly breaches ASTM D6980 maximum allowable 0.0200%."
                ),
                "containment_actions": (
                    "WMS Staging Bay B-08 locked from picking. Supplier issued CAR #CAR-2026-11."
                ),
                "hold_declared": True,
                "status": NcrStatus.OPEN_CONTAINED,
                "created_by": user_map["qc_inspector"],
            },
            {
                "source_domain": SourceDomain.OQC,
                "severity": SeverityLevel.MINOR,
                "target_type": TargetType.FINISHED_GOODS,
                "target_identifier": "PALLET-PL-9024",
                "defect_description": (
                    "DataMatrix carton barcode readability grade C (below required grade B threshold)."
                ),
                "containment_actions": (
                    "All 25 cartons 100% re-labeled and verified with Cognex handheld imager. "
                    "[Resolution]: Verified 100% readable."
                ),
                "hold_declared": False,
                "status": NcrStatus.CLOSED,
                "created_by": user_map["qa_manager"],
            },
        ]
        ncr_map = {}
        for idx, nc in enumerate(ncrs_config, start=1):
            ncr_num = f"NCR-2026-000{idx}"
            ncr, _ = NonConformanceReport.objects.update_or_create(
                ncr_number=ncr_num,
                defaults=nc,
            )
            ncr_map[ncr_num] = ncr

        self.stdout.write(self.style.SUCCESS(f"  Initialized {len(ncrs_config)} Non-Conformance Reports."))

        # ---------------------------------------------------------------------
        # 7. MATERIAL REVIEW BOARD (MRB) FOUR-EYES DELIBERATION DOCKET
        # ---------------------------------------------------------------------
        self.stdout.write("7. Seeding Material Review Board deliberations & Four-Eyes votes...")
        ncr_crit = ncr_map["NCR-2026-0001"]
        mrb_case, _ = MrbCase.objects.update_or_create(
            ncr=ncr_crit,
            defaults={
                "chairperson": user_map["qa_manager"],
                "proposed_disposition": DispositionType.USE_AS_IS,
                "concession_rationale": (
                    "Flash deviation is localized to non-visible underbody mounting tab (0.10mm vs 0.05mm max). "
                    "No structural or fit impact."
                ),
                "customer_approval_required": True,
                "customer_approval_doc": "OEM-CONCESSION-DOC-2026-8819",
                "status": MrbStatus.IN_DELIBERATION,
            },
        )

        # Cast Four-Eyes votes: Quality Manager & Chief Engineer both approve
        MrbVote.objects.update_or_create(
            mrb_case=mrb_case,
            voter=user_map["qa_manager"],
            defaults={
                "voter_role": MrbRole.QUALITY_MANAGER,
                "vote": VoteChoice.APPROVE,
                "comments": "Quality risk evaluated. Form-fit-function verified acceptable for underbody trim.",
                "signature_token": "SHA256:7b8e9102c4819ad83ef091a134810294",
            },
        )
        MrbVote.objects.update_or_create(
            mrb_case=mrb_case,
            voter=user_map["chief_engineer"],
            defaults={
                "voter_role": MrbRole.CHIEF_ENGINEER,
                "vote": VoteChoice.APPROVE,
                "comments": (
                    "Tooling cavity pressure analyzed. Clamping force adjusted to 190 bar to prevent recurrence."
                ),
                "signature_token": "SHA256:39a8bc4710398ef29182309124018294",
            },
        )

        self.stdout.write(self.style.SUCCESS("  Initialized active MRB deliberation ready for Four-Eyes finalization."))

        # ---------------------------------------------------------------------
        # 8. MULTI-TIER GENEALOGY & BLAST RADIUS GRAPH
        # ---------------------------------------------------------------------
        self.stdout.write("8. Seeding multi-tier supply chain lot genealogy graph...")
        # Full pedigree: RESIN -> HOPPER -> RUN -> CARTON -> PALLET -> SHIPMENT
        genealogy_nodes = [
            # Tier 1: Resin Lot
            {
                "node_type": NodeType.RESIN_LOT,
                "node_identifier": "RESIN-LOT-PA66-2026-081",
                "parent_identifier": None,
                "metadata": {"supplier": "DuPont", "polymer": "PA66-GF30", "received_kg": 5000},
            },
            # Tier 2: Drying Hopper
            {
                "node_type": NodeType.HOPPER,
                "node_identifier": "HOPPER-DRY-02",
                "parent_identifier": "RESIN-LOT-PA66-2026-081",
                "metadata": {"dryer_temp_c": 80, "dew_point_c": -42, "residence_time_hrs": 4.5},
            },
            # Tier 3: IMM Machine Production Run
            {
                "node_type": NodeType.RUN,
                "node_identifier": "IMM-01-RUN-882",
                "parent_identifier": "HOPPER-DRY-02",
                "metadata": {"machine": "IMM-01", "mold": "MOLD-TRIM-4C", "shots_produced": 800},
            },
            # Tier 4: Serialized Cartons
            {
                "node_type": NodeType.CARTON,
                "node_identifier": "CARTON-CTN-7701",
                "parent_identifier": "IMM-01-RUN-882",
                "metadata": {"cavities": [1, 2], "qty_pieces": 200, "weight_kg": 18.4},
            },
            {
                "node_type": NodeType.CARTON,
                "node_identifier": "CARTON-CTN-7702",
                "parent_identifier": "IMM-01-RUN-882",
                "metadata": {"cavities": [3, 4], "qty_pieces": 200, "weight_kg": 18.5},
            },
            # Tier 5: Warehouse Pallets
            {
                "node_type": NodeType.PALLET,
                "node_identifier": "PALLET-PL-9021",
                "parent_identifier": "CARTON-CTN-7701",
                "metadata": {"carton_count": 5, "total_units": 1000, "warehouse_bay": "WMS-BAY-C04"},
            },
            {
                "node_type": NodeType.PALLET,
                "node_identifier": "PALLET-PL-9022",
                "parent_identifier": "CARTON-CTN-7702",
                "metadata": {"carton_count": 4, "total_units": 800, "warehouse_bay": "WMS-BAY-C05"},
            },
            # Tier 6: Customer Logistics Shipments
            {
                "node_type": NodeType.SHIPMENT,
                "node_identifier": "SHIPMENT-SH-4491",
                "parent_identifier": "PALLET-PL-9021",
                "metadata": {
                    "carrier": "DHL Automotive Logistics",
                    "bol_number": "BOL-882910-A",
                    "destination_plant": "OEM Assembly Plant Wolfsburg",
                },
            },
            {
                "node_type": NodeType.SHIPMENT,
                "node_identifier": "SHIPMENT-SH-4492",
                "parent_identifier": "PALLET-PL-9022",
                "metadata": {
                    "carrier": "Schenker Freight",
                    "bol_number": "BOL-882911-B",
                    "destination_plant": "OEM Assembly Plant Dingolfing",
                },
            },
        ]
        for node in genealogy_nodes:
            TraceabilityNode.objects.update_or_create(
                node_identifier=node["node_identifier"],
                defaults={
                    "node_type": node["node_type"],
                    "parent_identifier": node["parent_identifier"],
                    "metadata_snapshot": node["metadata"],
                },
            )

        self.stdout.write(self.style.SUCCESS(f"  Indexed {len(genealogy_nodes)} supply chain genealogy nodes."))

        # ---------------------------------------------------------------------
        # 9. 21 CFR PART 11 AUDIT TRAIL ELECTRONIC SIGNATURES
        # ---------------------------------------------------------------------
        self.stdout.write("9. Recording 21 CFR Part 11 audit manifestation records...")
        first_iqc = IqcInspectionTask.objects.filter(lot_number="LOT-PA66-2026-081").first()
        audit_events = [
            {
                "action_type": "CREATE",
                "entity_type": "IqcInspectionTask",
                "entity_id": first_iqc.id,
                "badge_number": "QC-INSP-001",
                "signature_manifestation": (
                    "Resin lot LOT-PA66-2026-081 verified and released to Available by QC-INSP-001"
                ),
            },
            {
                "action_type": "QUALITY_HOLD_DECLARED",
                "entity_type": "NonConformanceReport",
                "entity_id": ncr_crit.id,
                "badge_number": "QA-MGR-001",
                "signature_manifestation": f"Emergency Quality Hold declared by QA-MGR-001 for {ncr_crit.ncr_number}",
            },
            {
                "action_type": "MRB_VOTE_CAST",
                "entity_type": "MrbVote",
                "entity_id": mrb_case.id,
                "badge_number": "ENG-CHIEF-001",
                "signature_manifestation": "Four-Eyes Vote APPROVE cast with SHA-256 seal by ENG-CHIEF-001",
            },
        ]
        for ae in audit_events:
            AuditTrailEvent.objects.create(
                action_type=ae["action_type"],
                entity_type=ae["entity_type"],
                entity_id=ae["entity_id"],
                badge_number=ae["badge_number"],
                payload_snapshot={"seeded": True, "timestamp": timezone.now().isoformat()},
                signature_manifestation=ae["signature_manifestation"],
            )

        self.stdout.write(self.style.SUCCESS("  Recorded 21 CFR Part 11 electronic audit trail logs."))

        # ---------------------------------------------------------------------
        # SUMMARY
        # ---------------------------------------------------------------------
        self.stdout.write(self.style.SUCCESS("\n🎉 Factory Demo Data Seeding Complete!"))
        self.stdout.write("Demo Logins:")
        self.stdout.write("  • Quality Director:  admin / AdminPass123! (Badge: QA-DIR-001)")
        self.stdout.write("  • Quality Manager:   qa_manager / ManagerPass123! (Badge: QA-MGR-001)")
        self.stdout.write("  • Chief Engineer:    chief_engineer / EngineerPass123! (Badge: ENG-CHIEF-001)")
        self.stdout.write("  • QC Inspector:      qc_inspector / InspectorPass123! (Badge: QC-INSP-001)")
        self.stdout.write("  • Shift Lead:        ops_lead / OperatorPass123! (Badge: OPS-LEAD-001)")
        self.stdout.write("\nKey Demo Entities:")
        self.stdout.write("  • Quality Hold NCR:  NCR-2026-0001 (Critical hold on IMM-03-RUN-884)")
        self.stdout.write("  • MRB Deliberation:  Case linked to NCR-2026-0001 (Four-Eyes dual approval ready)")
        self.stdout.write("  • Backward Trace:    Query 'SHIPMENT-SH-4491' in /traceability/")
        self.stdout.write("  • Blast Radius:      Query 'RESIN-LOT-PA66-2026-081' (forward) in /traceability/")
