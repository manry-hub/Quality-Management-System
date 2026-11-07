import uuid
from django.conf import settings
from django.db import models


class OqcInspection(models.Model):
    STATUS_CHOICES = (
        ("PENDING", "Pending"),
        ("RELEASED_FOR_SHIPMENT", "Released for Shipment"),
        ("REJECTED", "Rejected"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pallet_barcode = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Finished goods pallet / carton DataMatrix barcode",
    )
    part = models.ForeignKey(
        "master_data.Part",
        on_delete=models.PROTECT,
        related_name="oqc_inspections",
    )
    batch_quantity = models.PositiveIntegerField(
        default=1000,
        help_text="Total finished goods lot quantity for ISO 2859-1 sampling",
    )
    sample_size = models.PositiveIntegerField(
        help_text="Calculated ISO 2859-1 Level II normal inspection sample count",
    )
    defects_found = models.PositiveIntegerField(
        default=0,
        help_text="Attribute defect count; c=0 strict zero-defect threshold",
    )
    packaging_box_intact = models.BooleanField(
        default=True,
        help_text="Corrugated box structural integrity & clean sealing",
    )
    esd_bag_sealed = models.BooleanField(
        default=True,
        help_text="Anti-static ESD bag hermetically sealed",
    )
    desiccant_present = models.BooleanField(
        default=True,
        help_text="Desiccant pouch present inside packaging",
    )
    datamatrix_verified = models.BooleanField(
        default=True,
        help_text="2D DataMatrix label verified scannable and matched to lot",
    )
    coc_number = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        help_text="Generated Certificate of Conformance ID",
    )
    coc_file_path = models.CharField(max_length=500, blank=True, default="")
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default="PENDING",
        db_index=True,
    )
    inspected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="oqc_inspections",
    )
    inspected_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "oqc_inspections"
        ordering = ["-created_at"]
        verbose_name = "OQC Inspection"
        verbose_name_plural = "OQC Inspections"

    def __str__(self):
        return f"OQC-{self.pallet_barcode} ({self.get_status_display()})"


class OqcDefectItem(models.Model):
    SEVERITY_CHOICES = (
        ("CRITICAL", "Critical"),
        ("MAJOR", "Major"),
        ("MINOR", "Minor"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    inspection = models.ForeignKey(
        OqcInspection,
        on_delete=models.CASCADE,
        related_name="defect_items",
    )
    defect_type = models.CharField(
        max_length=100,
        help_text="Defect mode (e.g. SINK_MARK, FLASH, SCRATCH, WARPAGE)",
    )
    severity = models.CharField(
        max_length=50,
        choices=SEVERITY_CHOICES,
        default="MAJOR",
    )
    defect_count = models.PositiveIntegerField(default=1)
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "oqc_defect_items"
        ordering = ["-created_at"]
        verbose_name = "OQC Defect Item"
        verbose_name_plural = "OQC Defect Items"

    def __str__(self):
        return f"{self.defect_type} ({self.severity}) x{self.defect_count}"
