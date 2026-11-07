import uuid
from django.conf import settings
from django.db import models


class IqcInspectionTask(models.Model):
    STATUS_CHOICES = (
        ("PENDING_INSPECTION", "Pending Inspection"),
        ("IN_INSPECTION", "In Inspection"),
        ("ACCEPTED", "Accepted"),
        ("REJECTED", "Rejected"),
    )

    DISPOSITION_CHOICES = (
        ("NONE", "None"),
        ("RELEASE_TO_AVAILABLE", "Release to Available"),
        ("QUARANTINE_REJECTED", "Quarantine / Rejected"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wms_event_id = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="Idempotency key from companion WMS intake webhook",
    )
    lot_number = models.CharField(max_length=100, db_index=True)
    material = models.ForeignKey(
        "master_data.ResinMaterial",
        on_delete=models.PROTECT,
        related_name="iqc_tasks",
    )
    supplier_code = models.CharField(max_length=100, db_index=True)
    quantity_kg = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default="PENDING_INSPECTION",
        db_index=True,
    )
    disposition = models.CharField(
        max_length=50,
        choices=DISPOSITION_CHOICES,
        default="NONE",
    )
    rejection_reason = models.TextField(blank=True, default="")
    coa_file_path = models.CharField(max_length=500, blank=True, default="")
    coa_moisture_pct = models.DecimalField(
        max_digits=6, decimal_places=4, null=True, blank=True
    )
    coa_mfi_value = models.DecimalField(
        max_digits=8, decimal_places=3, null=True, blank=True
    )
    coa_density = models.DecimalField(
        max_digits=6, decimal_places=4, null=True, blank=True
    )
    physical_moisture_pct = models.DecimalField(
        max_digits=6, decimal_places=4, null=True, blank=True
    )
    physical_mfi_value = models.DecimalField(
        max_digits=8, decimal_places=3, null=True, blank=True
    )
    inspected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="iqc_inspections",
    )
    inspected_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "iqc_inspection_tasks"
        ordering = ["-created_at"]
        verbose_name = "IQC Inspection Task"
        verbose_name_plural = "IQC Inspection Tasks"

    def __str__(self):
        return f"IQC-{self.lot_number} ({self.get_status_display()})"


class IqcSample(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(
        IqcInspectionTask,
        on_delete=models.CASCADE,
        related_name="samples",
    )
    sample_number = models.PositiveIntegerField()
    bag_pallet_barcode = models.CharField(max_length=100)
    visual_inspection_passed = models.BooleanField(default=True)
    moisture_pct = models.DecimalField(
        max_digits=6, decimal_places=4, null=True, blank=True
    )
    mfi_value = models.DecimalField(
        max_digits=8, decimal_places=3, null=True, blank=True
    )
    contamination_detected = models.BooleanField(default=False)
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "iqc_samples"
        ordering = ["sample_number"]
        verbose_name = "IQC Sample"
        verbose_name_plural = "IQC Samples"

    def __str__(self):
        return f"{self.task.lot_number} Sample #{self.sample_number}"
