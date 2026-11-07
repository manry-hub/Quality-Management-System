import uuid
from django.db import models
from django.conf import settings
from apps.master_data.models import ResinMaterial


class SupplierTierChoices(models.TextChoices):
    TIER_1 = "TIER_1", "Tier 1 (Direct Automotive)"
    TIER_2 = "TIER_2", "Tier 2 (Sub-Supplier)"


class SupplierStatusChoices(models.TextChoices):
    APPROVED = "APPROVED", "Approved Supplier"
    CONDITIONAL = "CONDITIONAL", "Conditional / Probationary"
    DISQUALIFIED = "DISQUALIFIED", "Disqualified / Barred"


class CoaStatusChoices(models.TextChoices):
    PENDING_REVIEW = "PENDING_REVIEW", "Pending Review"
    APPROVED = "APPROVED", "Approved / Compliant"
    REJECTED = "REJECTED", "Rejected / Out of Spec"


class ScorecardGradeChoices(models.TextChoices):
    GRADE_A = "GRADE_A", "Grade A (Preferred >= 95%)"
    GRADE_B = "GRADE_B", "Grade B (Qualified 85-94%)"
    GRADE_C = "GRADE_C", "Grade C (Conditional 70-84%)"
    GRADE_D = "GRADE_D", "Grade D (Disqualified < 70%)"


class Supplier(models.Model):
    """
    IATF 16949 Section 8.4 External Provider & Supplier Profile.
    Tracks certifications, contact metadata, and quality status.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True, db_index=True, help_text="e.g. VEND-BASF")
    name = models.CharField(max_length=200)
    country = models.CharField(max_length=100, default="Germany")
    tier = models.CharField(max_length=20, choices=SupplierTierChoices.choices, default=SupplierTierChoices.TIER_1)
    status = models.CharField(
        max_length=50,
        choices=SupplierStatusChoices.choices,
        default=SupplierStatusChoices.APPROVED,
        db_index=True,
    )
    contact_email = models.EmailField(blank=True, default="")
    quality_contact_name = models.CharField(max_length=150, blank=True, default="")
    iso_certification = models.CharField(max_length=100, default="IATF 16949:2016 / ISO 9001")
    cert_expiry_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "sqa_suppliers"
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} — {self.name} [{self.status}]"


class CertificateOfAnalysis(models.Model):
    """
    Supplier digital Certificate of Analysis (CoA) submitted with resin shipments.
    Contains chemical & rheological parameter test results.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    coa_number = models.CharField(max_length=50, unique=True, db_index=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name="coas")
    material = models.ForeignKey(ResinMaterial, on_delete=models.PROTECT, related_name="coas")
    lot_number = models.CharField(max_length=100, db_index=True)
    manufacture_date = models.DateField()
    expiration_date = models.DateField(null=True, blank=True)
    parameters = models.JSONField(
        default=dict,
        help_text="Chemical/physical test data, e.g. {'moisture_pct': 0.012, 'mfi_g_10min': 12.4, 'density': 1.14}",
    )
    compliance_score = models.DecimalField(max_digits=5, decimal_places=2, default=100.0)
    status = models.CharField(
        max_length=50,
        choices=CoaStatusChoices.choices,
        default=CoaStatusChoices.PENDING_REVIEW,
        db_index=True,
    )
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_coas",
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    deviation_notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "sqa_coas"
        ordering = ["-created_at"]

    def __str__(self):
        return f"CoA {self.coa_number} ({self.lot_number}) [{self.status}]"


class SupplierScorecard(models.Model):
    """
    Periodic supplier quality scorecard evaluating lot acceptance, PPM defect rate, and CoA compliance.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name="scorecards")
    period_label = models.CharField(max_length=50, help_text="e.g. 2026-Q4 or 2026-11")
    total_lots_supplied = models.PositiveIntegerField(default=0)
    accepted_lots = models.PositiveIntegerField(default=0)
    rejected_lots = models.PositiveIntegerField(default=0)
    ppm_defect_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    on_time_delivery_pct = models.DecimalField(max_digits=5, decimal_places=2, default=100.0)
    coa_compliance_pct = models.DecimalField(max_digits=5, decimal_places=2, default=100.0)
    grade = models.CharField(
        max_length=20,
        choices=ScorecardGradeChoices.choices,
        default=ScorecardGradeChoices.GRADE_A,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "sqa_supplier_scorecards"
        ordering = ["-created_at"]
        unique_together = ("supplier", "period_label")

    def __str__(self):
        return f"{self.supplier.code} Scorecard {self.period_label} — {self.grade} ({self.ppm_defect_rate} PPM)"
