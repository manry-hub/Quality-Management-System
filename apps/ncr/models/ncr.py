import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


class SourceDomain(models.TextChoices):
    IQC = "IQC", "Incoming Quality Control"
    IPQC = "IPQC", "In-Process Quality Control"
    OQC = "OQC", "Outgoing Quality Control"
    CUSTOMER_RMA = "CUSTOMER_RMA", "Customer RMA / Return"
    INTERNAL_AUDIT = "INTERNAL_AUDIT", "Internal Quality Audit"


class SeverityLevel(models.TextChoices):
    CRITICAL = "CRITICAL", "Critical (Safety / Form-Fit-Function)"
    MAJOR = "MAJOR", "Major (Quality Standard Breach)"
    MINOR = "MINOR", "Minor (Cosmetic / Packaging)"


class NcrStatus(models.TextChoices):
    OPEN_CONTAINED = "OPEN_CONTAINED", "Open / Contained (QA Hold Active)"
    IN_MRB_REVIEW = "IN_MRB_REVIEW", "In MRB Deliberation"
    DISPOSITIONED = "DISPOSITIONED", "Dispositioned by MRB"
    CLOSED = "CLOSED", "Closed / Action Verified"


class TargetType(models.TextChoices):
    MATERIAL_LOT = "MATERIAL_LOT", "Raw Polymer Material Lot"
    IN_PROCESS_RUN = "IN_PROCESS_RUN", "IMM Production Run"
    FINISHED_GOODS = "FINISHED_GOODS", "Finished Goods Pallet"
    TOOLING_CAVITY = "TOOLING_CAVITY", "Mold Tooling Cavity"


class DispositionType(models.TextChoices):
    REWORK = "REWORK", "Rework (Regrind / Secondary Op)"
    REPAIR = "REPAIR", "Repair Tooling"
    SCRAP = "SCRAP", "Scrap Material"
    USE_AS_IS = "USE_AS_IS", "Use-As-Is (Concession Sign-Off)"
    RETURN_TO_SUPPLIER = "RETURN_TO_SUPPLIER", "Return to Supplier (RTV)"
    SORTING = "SORTING", "100% Sorting / Segregation"
    REINSPECTION = "REINSPECTION", "Re-inspection"


def generate_ncr_number():
    year = timezone.now().year
    prefix = f"NCR-{year}-"
    last_ncr = (
        NonConformanceReport.objects.filter(ncr_number__startswith=prefix)
        .order_by("-ncr_number")
        .first()
    )
    if last_ncr:
        try:
            seq = int(last_ncr.ncr_number.split("-")[-1]) + 1
        except (ValueError, IndexError):
            seq = 1
    else:
        seq = 1
    return f"{prefix}{seq:04d}"


class NonConformanceReport(models.Model):
    """
    NCR Master Record (IATF 16949 §8.7 & 21 CFR Part 11).
    Broadcasts multi-system Quality Hold across WMS and MES upon declaration.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ncr_number = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        default=generate_ncr_number,
    )
    source_domain = models.CharField(
        max_length=50,
        choices=SourceDomain.choices,
        db_index=True,
    )
    severity = models.CharField(
        max_length=50,
        choices=SeverityLevel.choices,
        db_index=True,
    )
    status = models.CharField(
        max_length=50,
        choices=NcrStatus.choices,
        default=NcrStatus.OPEN_CONTAINED,
        db_index=True,
    )
    target_type = models.CharField(
        max_length=50,
        choices=TargetType.choices,
    )
    target_identifier = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Lot Number, Machine Run ID, Pallet Barcode, or Cavity ID",
    )
    defect_description = models.TextField(
        help_text="Detailed failure mode, tolerance breach, or visual defect description",
    )
    containment_actions = models.TextField(
        blank=True,
        default="",
        help_text="Immediate containment steps executed (e.g. hopper dump, bin segregation)",
    )
    hold_declared = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Whether multi-system QA hold is active across WMS picking and MES loading",
    )
    disposition_type = models.CharField(
        max_length=50,
        choices=DispositionType.choices,
        blank=True,
        null=True,
        db_index=True,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_ncrs",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "non_conformance_reports"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["target_identifier", "hold_declared"], name="idx_ncr_target_hold"),
            models.Index(fields=["source_domain", "status"], name="idx_ncr_domain_status"),
        ]

    def __str__(self):
        return f"{self.ncr_number} [{self.severity}] - {self.target_identifier} ({self.status})"
