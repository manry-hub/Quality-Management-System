import uuid
from django.db import models
from apps.master_data.models import Part
from apps.ncr.models.ncr import NonConformanceReport


class DefectTypeChoices(models.TextChoices):
    FLASH = "FLASH", "Flash / Parting Line Burrs"
    SHORT_SHOT = "SHORT_SHOT", "Short Shot / Incomplete Cavity Fill"
    SINK_MARK = "SINK_MARK", "Sink Mark / Thermal Shrinkage"
    SPLAY_MARK = "SPLAY_MARK", "Splay / Moisture Silver Streaks"
    BURN_MARK = "BURN_MARK", "Burn Mark / Dieseling"
    JETTING = "JETTING", "Jetting / Gate Snake Lines"
    VOID = "VOID", "Internal / Surface Vacuum Void"
    WARPAGE = "WARPAGE", "Dimensional Warpage / Distortion"
    NO_DEFECT = "NO_DEFECT", "Clean Shot / Conforming"


class DefectSeverityChoices(models.TextChoices):
    ACCEPTABLE = "ACCEPTABLE", "Acceptable / Conforming"
    MINOR = "MINOR", "Minor Defect (Cosmetic)"
    MAJOR = "MAJOR", "Major Defect (Functional/Aesthetic Risk)"
    CRITICAL = "CRITICAL", "Critical Defect (Zero Tolerance / Assembly Stop)"


class VisionActionChoices(models.TextChoices):
    CLEARED = "CLEARED", "Cleared for Conveyor"
    REJECT_DIVERTED = "REJECT_DIVERTED", "Diverted to Automated Scrap Bin"
    NCR_HOLD_TRIGGERED = "NCR_HOLD_TRIGGERED", "Emergency Quality Hold / NCR Triggered"


class VisionInspectionStation(models.Model):
    """
    Edge AI Camera Station installed on injection molding cell conveyor or robot arm.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    station_code = models.CharField(max_length=50, unique=True, db_index=True, help_text="e.g. CAM-IMM03-TOP")
    name = models.CharField(max_length=150)
    line_cell = models.CharField(max_length=100, default="IMM Cell Line 3")
    camera_model = models.CharField(max_length=100, default="Basler ace 2 Pro 4K GigE")
    resolution = models.CharField(max_length=50, default="3840x2160")
    confidence_threshold = models.DecimalField(max_digits=4, decimal_places=3, default=0.850)
    is_online = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "vision_stations"
        ordering = ["station_code"]

    def __str__(self):
        return f"{self.station_code}: {self.name} [{'ONLINE' if self.is_online else 'OFFLINE'}]"


class VisionDefectInspection(models.Model):
    """
    Individual shot visual defect inference result with bounding boxes and automated quarantine action.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    station = models.ForeignKey(VisionInspectionStation, on_delete=models.CASCADE, related_name="inspections")
    part = models.ForeignKey(Part, on_delete=models.CASCADE, related_name="vision_inspections")
    inspection_timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    shot_number = models.PositiveIntegerField(default=1)
    cavity_number = models.PositiveIntegerField(default=1)
    primary_defect_type = models.CharField(
        max_length=50,
        choices=DefectTypeChoices.choices,
        default=DefectTypeChoices.NO_DEFECT,
        db_index=True,
    )
    confidence_score = models.DecimalField(max_digits=5, decimal_places=4, default=0.9500)
    severity = models.CharField(
        max_length=50,
        choices=DefectSeverityChoices.choices,
        default=DefectSeverityChoices.ACCEPTABLE,
        db_index=True,
    )
    bounding_boxes = models.JSONField(
        default=list,
        help_text="List of detection dicts: [{'label': 'FLASH', 'bbox': [x, y, w, h], 'confidence': 0.94}]",
    )
    image_path = models.CharField(max_length=255, blank=True, default="")
    auto_action_taken = models.CharField(
        max_length=50,
        choices=VisionActionChoices.choices,
        default=VisionActionChoices.CLEARED,
    )
    ncr = models.ForeignKey(
        NonConformanceReport,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="vision_inspections",
    )

    class Meta:
        db_table = "vision_defect_inspections"
        ordering = ["-inspection_timestamp"]

    def __str__(self):
        return f"Shot #{self.shot_number} Cav #{self.cavity_number} — {self.primary_defect_type} ({self.severity})"
