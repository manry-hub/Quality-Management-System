import uuid
from django.db import models


class PolymerTypeChoices(models.TextChoices):
    PP = "PP", "Polypropylene"
    ABS = "ABS", "Acrylonitrile Butadiene Styrene"
    PC = "PC", "Polycarbonate"
    PA66 = "PA66", "Polyamide (Nylon 66)"
    POM = "POM", "Polyoxymethylene (Acetal)"
    MASTERBATCH = "MASTERBATCH", "Color Masterbatch / Additive"


class ResinMaterial(models.Model):
    """
    Raw Resin & Polymer Material Master.
    Stores baseline CoA target specifications (Moisture %, MFI) for incoming QC verification.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    material_code = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="Raw material SKU (e.g. RES-PP-HOMO, RES-ABS-HI)"
    )
    material_name = models.CharField(max_length=255)
    polymer_type = models.CharField(
        max_length=50,
        choices=PolymerTypeChoices.choices,
        default=PolymerTypeChoices.PP,
        db_index=True
    )
    supplier_code = models.CharField(
        max_length=100,
        db_index=True,
        help_text="ERP Supplier Code reference (e.g. VEND-LOTTE, VEND-INEOS)"
    )
    target_moisture_max_pct = models.DecimalField(
        max_digits=6,
        decimal_places=4,
        default=0.0200,
        help_text="Maximum allowable moisture % before drying/hopper loading (e.g. 0.0200%)"
    )
    target_mfi_nominal = models.DecimalField(
        max_digits=8,
        decimal_places=3,
        help_text="Nominal Melt Flow Index (g/10min under ASTM D1238 / ISO 1133)"
    )
    target_mfi_tolerance = models.DecimalField(
        max_digits=8,
        decimal_places=3,
        help_text="Allowable deviation (+/- g/10min)"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "materials"
        verbose_name = "Resin Material"
        verbose_name_plural = "Resin Materials"
        ordering = ["material_code"]

    def __str__(self):
        return f"{self.material_code} — {self.material_name} ({self.polymer_type})"
