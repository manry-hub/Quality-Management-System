import uuid
from django.conf import settings
from django.db import models


class IpqcInspection(models.Model):
    INSPECTION_TYPES = (
        ("FIRST_PIECE_FAI", "First-Piece FAI"),
        ("HOURLY_PATROL", "Hourly Patrol"),
        ("SETUP_VALIDATION", "Setup Validation"),
    )

    DISPOSITION_CHOICES = (
        ("PENDING", "Pending"),
        ("RELEASED", "Released"),
        ("REJECTED", "Rejected"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    inspection_type = models.CharField(
        max_length=50,
        choices=INSPECTION_TYPES,
        default="FIRST_PIECE_FAI",
        db_index=True,
    )
    mes_run_id = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Target MES Production Run Identifier",
    )
    machine_code = models.CharField(
        max_length=50,
        db_index=True,
        help_text="Machine identifier (IMM-01 to IMM-10)",
    )
    mold_code = models.CharField(max_length=100, db_index=True)
    part = models.ForeignKey(
        "master_data.Part",
        on_delete=models.PROTECT,
        related_name="ipqc_inspections",
    )
    control_plan = models.ForeignKey(
        "quality_planning.ControlPlan",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ipqc_inspections",
    )
    disposition = models.CharField(
        max_length=50,
        choices=DISPOSITION_CHOICES,
        default="PENDING",
        db_index=True,
    )
    signature_token = models.CharField(
        max_length=512,
        blank=True,
        default="",
        help_text="Cryptographic HMAC-SHA256 release token dispatched to MES",
    )
    signed_at = models.DateTimeField(null=True, blank=True)
    cushion_mm = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True
    )
    peak_pressure_bar = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True
    )
    line_stop_triggered = models.BooleanField(
        default=False,
        help_text="Andon line stop status tripped by quality failure or telemetry drift",
    )
    line_stop_reason = models.TextField(blank=True, default="")
    inspected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ipqc_inspections",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ipqc_inspections"
        ordering = ["-created_at"]
        verbose_name = "IPQC Inspection"
        verbose_name_plural = "IPQC Inspections"

    def __str__(self):
        return f"IPQC-{self.machine_code}-{self.inspection_type} ({self.disposition})"


class IpqcCavitySample(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    inspection = models.ForeignKey(
        IpqcInspection,
        on_delete=models.CASCADE,
        related_name="cavity_samples",
    )
    cavity_number = models.PositiveIntegerField()
    shot_number = models.PositiveIntegerField(
        default=1,
        help_text="Shot sequence (e.g. 1, 2, 3 for consecutive FAI shots)",
    )
    characteristic_name = models.CharField(max_length=200)
    measured_value = models.DecimalField(max_digits=10, decimal_places=4)
    nominal_value = models.DecimalField(max_digits=10, decimal_places=4)
    usl = models.DecimalField(max_digits=10, decimal_places=4)
    lsl = models.DecimalField(max_digits=10, decimal_places=4)
    is_conforming = models.BooleanField(default=True)
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ipqc_cavity_samples"
        ordering = ["shot_number", "cavity_number"]
        verbose_name = "IPQC Cavity Sample"
        verbose_name_plural = "IPQC Cavity Samples"

    def __str__(self):
        return (
            f"Shot {self.shot_number} Cav {self.cavity_number}: "
            f"{self.characteristic_name} = {self.measured_value}"
        )
