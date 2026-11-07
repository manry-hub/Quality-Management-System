import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone


class ControlPlanStatusChoices(models.TextChoices):
    DRAFT = "DRAFT", "Draft in Authoring"
    UNDER_REVIEW = "UNDER_REVIEW", "Under QA Review"
    APPROVED = "APPROVED", "Approved for Production"
    OBSOLETE = "OBSOLETE", "Obsolete / Superseded"


class CharacteristicTypeChoices(models.TextChoices):
    VARIABLE = "VARIABLE", "Variable (Measurable Numeric)"
    ATTRIBUTE = "ATTRIBUTE", "Attribute (Visual / Pass-Fail)"


class SpecialCharChoices(models.TextChoices):
    SAFETY_CRITICAL = "SAFETY_CRITICAL", "Safety Critical (Inverted Delta)"
    MAJOR = "MAJOR", "Major Critical-to-Quality (Diamond)"
    MINOR = "MINOR", "Standard Minor Characteristic"


class ControlPlan(models.Model):
    """
    IATF 16949 Compliant Production Quality Control Plan.
    Authoritative reference for in-process and first-piece tolerance checking.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    part = models.ForeignKey(
        "master_data.Part",
        on_delete=models.CASCADE,
        related_name="control_plans",
        db_index=True
    )
    revision = models.CharField(max_length=20, default="REV-A", db_index=True)
    status = models.CharField(
        max_length=50,
        choices=ControlPlanStatusChoices.choices,
        default=ControlPlanStatusChoices.DRAFT,
        db_index=True
    )
    fmea_reference = models.CharField(
        max_length=100,
        blank=True,
        help_text="Reference AIAG-VDA PFMEA document number"
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_control_plans"
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    effective_date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "control_plans"
        verbose_name = "Control Plan"
        verbose_name_plural = "Control Plans"
        unique_together = ("part", "revision")
        ordering = ["part", "-revision"]

    def __str__(self):
        return f"Control Plan {self.part.part_number} [{self.revision}] — {self.status}"


class ControlPlanItem(models.Model):
    """
    Discrete CTQ characteristic item defined inside a Control Plan.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    control_plan = models.ForeignKey(
        ControlPlan,
        on_delete=models.CASCADE,
        related_name="items"
    )
    characteristic_name = models.CharField(
        max_length=255,
        help_text="e.g. Critical Bumper Width, Wall Thickness, Surface Flash"
    )
    characteristic_type = models.CharField(
        max_length=50,
        choices=CharacteristicTypeChoices.choices,
        default=CharacteristicTypeChoices.VARIABLE
    )
    special_char_class = models.CharField(
        max_length=50,
        choices=SpecialCharChoices.choices,
        null=True,
        blank=True
    )
    target_value = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Nominal target dimension"
    )
    usl = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Upper Specification Limit"
    )
    lsl = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Lower Specification Limit"
    )
    unit_of_measure = models.CharField(max_length=20, default="mm")
    tool_category = models.CharField(
        max_length=100,
        default="CMM",
        help_text="Required tool e.g. CMM, DIGITAL_CALIPER, OPTICAL_SCANNER"
    )
    sampling_frequency = models.CharField(
        max_length=100,
        default="FIRST_PIECE",
        help_text="e.g. FIRST_PIECE, HOURLY_PATROL, 1_PER_500_SHOTS"
    )
    sample_size = models.PositiveIntegerField(
        default=1,
        help_text="Number of parts sampled per cavity per cycle"
    )

    class Meta:
        db_table = "control_plan_items"
        verbose_name = "Control Plan Characteristic"
        verbose_name_plural = "Control Plan Characteristics"
        ordering = ["control_plan", "characteristic_name"]

    def __str__(self):
        return f"{self.characteristic_name} ({self.get_characteristic_type_display()})"
