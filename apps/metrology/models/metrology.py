import uuid
from django.db import models
from django.utils import timezone
from apps.master_data.models import Part


class GaugeTypeChoices(models.TextChoices):
    VERNIER_CALIPER = "VERNIER_CALIPER", "Digital Vernier Caliper (0-150mm)"
    DIGITAL_MICROMETER = "DIGITAL_MICROMETER", "Digital Outside Micrometer (0-25mm)"
    HEIGHT_GAUGE = "HEIGHT_GAUGE", "Digital Height Gauge"
    OPTICAL_COMPARATOR = "OPTICAL_COMPARATOR", "Optical Profile Projector"
    CMM_STATION = "CMM_STATION", "Coordinate Measuring Machine (CMM 3D)"
    MOISTURE_ANALYZER = "MOISTURE_ANALYZER", "Coulometric / Halogen Moisture Analyzer"
    MELT_FLOW_INDEXER = "MELT_FLOW_INDEXER", "Melt Flow Indexer (MFI ISO 1133)"


class GaugeStatusChoices(models.TextChoices):
    ACTIVE = "ACTIVE", "Active / In Calibration"
    OVERDUE = "OVERDUE", "Calibration Overdue (Inspection Lockout)"
    OUT_OF_SERVICE = "OUT_OF_SERVICE", "Out of Service / Damaged"


class MsaStudyTypeChoices(models.TextChoices):
    ANOVA_GAUGE_RR = "ANOVA_GAUGE_RR", "ANOVA Gauge R&R (AIAG MSA 4th Ed)"
    ATTRIBUTE_AGREEMENT = "ATTRIBUTE_AGREEMENT", "Attribute Agreement Analysis"


class MsaAcceptanceChoices(models.TextChoices):
    ACCEPTABLE = "ACCEPTABLE", "Acceptable (%GRR <= 10%, ndc >= 5)"
    MARGINAL = "MARGINAL", "Marginally Acceptable (10% < %GRR <= 30%)"
    UNACCEPTABLE = "UNACCEPTABLE", "Unacceptable (%GRR > 30% or ndc < 5)"


class Gauge(models.Model):
    """
    IATF 16949 Section 7.1.5 Measurement Systems & Gauge Registry.
    Maintains traceable calibration certificates and enforces automated floor measurement lockouts.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device_id = models.CharField(max_length=50, unique=True, db_index=True, help_text="e.g. GAGE-CAL-001, CMM-01")
    name = models.CharField(max_length=200)
    gauge_type = models.CharField(max_length=50, choices=GaugeTypeChoices.choices)
    serial_number = models.CharField(max_length=100)
    location = models.CharField(max_length=100, help_text="e.g. QC Lab 1, IMM Cell Line 3")
    resolution_mm = models.DecimalField(max_digits=8, decimal_places=4, default=0.0100)
    calibration_interval_months = models.PositiveIntegerField(default=12)
    last_calibration_date = models.DateField()
    next_calibration_due = models.DateField(db_index=True)
    status = models.CharField(
        max_length=50,
        choices=GaugeStatusChoices.choices,
        default=GaugeStatusChoices.ACTIVE,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "metrology_gauges"
        ordering = ["device_id"]

    def __str__(self):
        return f"{self.device_id} — {self.name} [{self.status}]"

    def is_calibration_valid(self) -> bool:
        return self.status == GaugeStatusChoices.ACTIVE and self.next_calibration_due >= timezone.now().date()


class GaugeCalibration(models.Model):
    """
    Periodic calibration record with NIST/ISO 17025 traceable calibration standard.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    gauge = models.ForeignKey(Gauge, on_delete=models.CASCADE, related_name="calibrations")
    certificate_number = models.CharField(max_length=100, unique=True)
    calibration_date = models.DateField()
    calibrated_by = models.CharField(max_length=150, help_text="Certified calibration lab or metrologist")
    as_found_condition = models.CharField(max_length=50, default="IN_TOLERANCE")
    as_left_condition = models.CharField(max_length=50, default="IN_TOLERANCE")
    uncertainty_budget_mm = models.DecimalField(max_digits=8, decimal_places=4, default=0.0020)
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "metrology_gauge_calibrations"
        ordering = ["-calibration_date"]

    def __str__(self):
        return f"Cal Cert {self.certificate_number} for {self.gauge.device_id}"


class MsaStudy(models.Model):
    """
    AIAG MSA 4th Edition ANOVA Gauge Repeatability & Reproducibility (Gauge R&R) Study.
    Calculates EV, AV, GRR, PV, %GRR, and Number of Distinct Categories (ndc).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    study_number = models.CharField(max_length=50, unique=True, db_index=True)
    gauge = models.ForeignKey(Gauge, on_delete=models.PROTECT, related_name="msa_studies")
    part = models.ForeignKey(Part, on_delete=models.PROTECT, related_name="msa_studies")
    characteristic_name = models.CharField(max_length=150)
    study_type = models.CharField(
        max_length=50,
        choices=MsaStudyTypeChoices.choices,
        default=MsaStudyTypeChoices.ANOVA_GAUGE_RR,
    )
    tolerance = models.DecimalField(max_digits=10, decimal_places=4, help_text="Specification tolerance (USL - LSL)")
    part_count = models.PositiveIntegerField(default=10)
    operator_count = models.PositiveIntegerField(default=3)
    trial_count = models.PositiveIntegerField(default=3)

    # 3D Array: data[part_idx][operator_idx][trial_idx]
    raw_data = models.JSONField(default=list, help_text="Matrix of trials per operator and part")

    # ANOVA Variance Results
    repeatability_ev = models.DecimalField(max_digits=10, decimal_places=5, null=True, blank=True)
    reproducibility_av = models.DecimalField(max_digits=10, decimal_places=5, null=True, blank=True)
    grr = models.DecimalField(max_digits=10, decimal_places=5, null=True, blank=True)
    part_variation_pv = models.DecimalField(max_digits=10, decimal_places=5, null=True, blank=True)
    total_variation_tv = models.DecimalField(max_digits=10, decimal_places=5, null=True, blank=True)
    grr_percent = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, help_text="%GRR")
    ndc = models.DecimalField(
        max_digits=6,
        decimal_places=1,
        null=True,
        blank=True,
        help_text="Number of Distinct Categories",
    )
    acceptance_status = models.CharField(
        max_length=50,
        choices=MsaAcceptanceChoices.choices,
        default=MsaAcceptanceChoices.ACCEPTABLE,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "metrology_msa_studies"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.study_number} — {self.gauge.device_id} ({self.acceptance_status})"
