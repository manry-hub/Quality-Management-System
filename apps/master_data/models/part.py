import uuid
from django.db import models


class Part(models.Model):
    """
    Automotive Molded Part Master catalog.
    Links engineering drawings, approved injection molds, and approved resin materials.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    part_number = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="Unique automotive SKU code (e.g. PRD-AUTO-BUMPER)"
    )
    part_name = models.CharField(max_length=255, db_index=True)
    drawing_number = models.CharField(max_length=100, db_index=True)
    drawing_revision = models.CharField(max_length=20, default="REV-A")
    approved_mold_codes = models.JSONField(
        default=list,
        help_text="List of approved tool codes e.g. ['MOLD-BUMP-2C']"
    )
    cavity_count = models.PositiveIntegerField(
        default=1,
        help_text="Total active cavities in the approved mold"
    )
    material_code = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Reference resin material code e.g. RES-PP-HOMO"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "parts"
        verbose_name = "Part"
        verbose_name_plural = "Parts"
        ordering = ["part_number"]

    def __str__(self):
        return f"{self.part_number} — {self.part_name} ({self.drawing_revision})"
