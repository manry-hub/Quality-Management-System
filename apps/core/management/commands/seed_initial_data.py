from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from apps.master_data.models import Part, ResinMaterial, PolymerTypeChoices


class Command(BaseCommand):
    help = "Seeds baseline IATF 16949 roles, standard automotive molded parts, and polymer resin master data."

    def handle(self, *args, **options):
        self.stdout.write("Seeding baseline IATF 16949 roles and master data...")

        # 1. Standard QA/QC Roles (Groups)
        roles = [
            "Quality Director",
            "Quality Manager",
            "QA Supervisor",
            "Quality Engineer",
            "Supplier Quality Engineer",
            "MRB Member",
            "IQC Inspector",
            "IPQC Inspector",
            "OQC Inspector",
            "Metrologist",
            "Document Controller",
            "Lead Quality Auditor",
        ]
        created_roles = 0
        for role_name in roles:
            _, created = Group.objects.get_or_create(name=role_name)
            if created:
                created_roles += 1

        self.stdout.write(self.style.SUCCESS(f"Initialized {len(roles)} IATF roles ({created_roles} new)."))

        # 2. Baseline Resin Materials
        materials = [
            {
                "material_code": "RES-PP-HOMO",
                "material_name": "Polypropylene Homopolymer (Automotive Grade)",
                "polymer_type": PolymerTypeChoices.PP,
                "supplier_code": "VEND-LOTTE",
                "target_moisture_max_pct": 0.0200,
                "target_mfi_nominal": 12.000,
                "target_mfi_tolerance": 1.500,
            },
            {
                "material_code": "RES-ABS-HI",
                "material_name": "High-Impact Acrylonitrile Butadiene Styrene",
                "polymer_type": PolymerTypeChoices.ABS,
                "supplier_code": "VEND-INEOS",
                "target_moisture_max_pct": 0.0200,
                "target_mfi_nominal": 18.000,
                "target_mfi_tolerance": 2.000,
            },
            {
                "material_code": "RES-PC-CLEAR",
                "material_name": "Polycarbonate Clear Optical Grade",
                "polymer_type": PolymerTypeChoices.PC,
                "supplier_code": "VEND-LOTTE",
                "target_moisture_max_pct": 0.0150,
                "target_mfi_nominal": 10.000,
                "target_mfi_tolerance": 1.000,
            },
        ]
        for mat in materials:
            ResinMaterial.objects.update_or_create(
                material_code=mat["material_code"],
                defaults=mat
            )
        self.stdout.write(self.style.SUCCESS(f"Seeded {len(materials)} baseline resin materials."))

        # 3. Baseline Automotive Parts
        parts = [
            {
                "part_number": "PRD-AUTO-BUMPER",
                "part_name": "Front Bumper Fascia (Aerodynamic)",
                "drawing_number": "DWG-BUMP-2026-X1",
                "drawing_revision": "REV-C",
                "approved_mold_codes": ["MOLD-BUMP-2C"],
                "cavity_count": 2,
                "material_code": "RES-PP-HOMO",
            },
            {
                "part_number": "PRD-DOOR-TRIM",
                "part_name": "Interior Door Trim Panel (Front Right)",
                "drawing_number": "DWG-TRIM-2026-R4",
                "drawing_revision": "REV-B",
                "approved_mold_codes": ["MOLD-TRIM-4C"],
                "cavity_count": 4,
                "material_code": "RES-ABS-HI",
            },
            {
                "part_number": "PRD-HVAC-DUCT",
                "part_name": "HVAC Air Distribution Duct (Under-Dash)",
                "drawing_number": "DWG-DUCT-2026-D2",
                "drawing_revision": "REV-A",
                "approved_mold_codes": ["MOLD-DUCT-2C"],
                "cavity_count": 2,
                "material_code": "RES-PP-HOMO",
            },
        ]
        for p in parts:
            Part.objects.update_or_create(
                part_number=p["part_number"],
                defaults=p
            )
        self.stdout.write(self.style.SUCCESS(f"Seeded {len(parts)} baseline automotive molded parts."))
