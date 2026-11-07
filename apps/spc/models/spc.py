import uuid
from django.db import models
from apps.master_data.models import Part


class ChartTypeChoices(models.TextChoices):
    XBAR_R = "XBAR_R", "X-bar and R Chart (Subgroup Mean & Range)"
    XBAR_S = "XBAR_S", "X-bar and S Chart (Subgroup Mean & Std Dev)"
    INDIVIDUAL_MR = "INDIVIDUAL_MR", "I-MR Chart (Individual & Moving Range)"


class SpcControlChart(models.Model):
    """
    Statistical Process Control (SPC) Chart Configuration & Parameters (ISO 21747 / AIAG SPC).
    Tracks variable quality characteristics for process capability and stability.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, help_text="e.g. IMM-02 Screw Cushion Monitor")
    part = models.ForeignKey(Part, on_delete=models.CASCADE, related_name="spc_charts")
    characteristic_name = models.CharField(max_length=150, help_text="e.g. Critical Bumper Width, Screw Cushion")
    chart_type = models.CharField(
        max_length=50,
        choices=ChartTypeChoices.choices,
        default=ChartTypeChoices.XBAR_R,
    )
    unit_of_measure = models.CharField(max_length=20, default="mm")
    subgroup_size = models.PositiveIntegerField(default=5)
    nominal = models.DecimalField(max_digits=10, decimal_places=4)
    usl = models.DecimalField(max_digits=10, decimal_places=4, help_text="Upper Specification Limit")
    lsl = models.DecimalField(max_digits=10, decimal_places=4, help_text="Lower Specification Limit")
    ucl = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True, help_text="Upper Control Limit")
    lcl = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True, help_text="Lower Control Limit")
    center_line = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)

    # ISO 21747 Capability Indices
    cp = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)
    cpk = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)
    pp = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)
    ppk = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "spc_control_charts"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} [{self.characteristic_name}]"


class SpcSubgroup(models.Model):
    """
    Periodic sample subgroup containing discrete measurements and evaluated Nelson Rules.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chart = models.ForeignKey(SpcControlChart, on_delete=models.CASCADE, related_name="subgroups")
    subgroup_number = models.PositiveIntegerField(db_index=True)
    sample_values = models.JSONField(default=list, help_text="Array of individual numeric measurements")
    sample_size = models.PositiveIntegerField(default=5)
    mean = models.DecimalField(max_digits=10, decimal_places=4)
    range_val = models.DecimalField(max_digits=10, decimal_places=4)
    std_dev = models.DecimalField(max_digits=10, decimal_places=4)
    nelson_rules_violated = models.JSONField(default=list, help_text="List of Nelson rule numbers violated (1 to 8)")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "spc_subgroups"
        ordering = ["subgroup_number"]
        unique_together = ("chart", "subgroup_number")

    def __str__(self):
        return f"{self.chart.name} Subgroup #{self.subgroup_number} (Mean={self.mean})"
