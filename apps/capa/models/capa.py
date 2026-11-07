import uuid
from django.db import models
from django.conf import settings
from apps.ncr.models.ncr import NonConformanceReport


class CapaDisciplineChoices(models.TextChoices):
    D1_TEAM = "D1_TEAM", "D1: Establish the Team"
    D2_PROBLEM = "D2_PROBLEM", "D2: Describe the Problem (5W2H)"
    D3_CONTAINMENT = "D3_CONTAINMENT", "D3: Interim Containment Actions (ICA)"
    D4_ROOT_CAUSE = "D4_ROOT_CAUSE", "D4: Root Cause Analysis (5-Why & Fishbone)"
    D5_PCA_CHOSEN = "D5_PCA_CHOSEN", "D5: Permanent Corrective Actions (PCA)"
    D6_PCA_IMPLEMENTED = "D6_PCA_IMPLEMENTED", "D6: Implement & Validate PCA"
    D7_PREVENTION = "D7_PREVENTION", "D7: Prevent Recurrence (Control Plan / FMEA)"
    D8_CLOSED = "D8_CLOSED", "D8: Congratulate Team & Close"


class CapaStatusChoices(models.TextChoices):
    OPEN = "OPEN", "Open (In Investigation)"
    IN_PROGRESS = "IN_PROGRESS", "In Progress (Actions Deployed)"
    UNDER_VOE = "UNDER_VOE", "Under Verification of Effectiveness (VoE)"
    CLOSED = "CLOSED", "Closed / Verified"


class VoeMilestoneChoices(models.TextChoices):
    DAY_30 = "30_DAY", "30-Day Checkpoint"
    DAY_60 = "60_DAY", "60-Day Checkpoint"
    DAY_90 = "90_DAY", "90-Day Final Closure Checkpoint"


class Capa8dRecord(models.Model):
    """
    IATF 16949 Section 10.2 Eight Disciplines (8D) Problem Solving Record.
    Drives systematic root-cause elimination using 5-Why and 6M Ishikawa Fishbone.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    capa_number = models.CharField(max_length=50, unique=True, db_index=True)
    title = models.CharField(max_length=255)
    ncr = models.ForeignKey(
        NonConformanceReport,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="capas",
        help_text="Originating Non-Conformance Report",
    )
    current_discipline = models.CharField(
        max_length=50,
        choices=CapaDisciplineChoices.choices,
        default=CapaDisciplineChoices.D1_TEAM,
    )
    status = models.CharField(
        max_length=50,
        choices=CapaStatusChoices.choices,
        default=CapaStatusChoices.OPEN,
        db_index=True,
    )

    # D1: Team
    champion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="championed_capas",
    )
    leader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="led_capas",
    )
    team_members = models.JSONField(default=list, help_text="List of cross-functional team member names and roles")

    # D2: Problem Statement (5W2H)
    d2_problem_statement = models.TextField(help_text="Who, What, Where, When, Why, How, How Many")

    # D3: Interim Containment
    d3_containment_action = models.TextField(blank=True, default="")
    d3_containment_verified_at = models.DateTimeField(null=True, blank=True)

    # D4: Root Cause (5-Why and 6M Fishbone)
    d4_root_cause_5why = models.JSONField(
        default=list,
        help_text="List of dicts: [{'why': 'Why did flash occur?', 'answer': 'Clamp pressure dropped.'}]",
    )
    d4_fishbone_data = models.JSONField(
        default=dict,
        help_text="Dict of 6M categories: man, machine, material, method, measurement, milieu",
    )
    d4_root_cause_summary = models.TextField(blank=True, default="")

    # D5 & D6: PCA
    d5_permanent_corrective_actions = models.TextField(blank=True, default="")
    d6_validation_results = models.TextField(blank=True, default="")
    d6_implementation_date = models.DateField(null=True, blank=True)

    # D7: Prevention & Document Updates
    d7_preventive_actions = models.TextField(blank=True, default="")
    fmea_updated = models.BooleanField(default=False)
    control_plan_updated = models.BooleanField(default=False)

    # D8: Team Recognition & Closure
    d8_closure_notes = models.TextField(blank=True, default="")
    closed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "capa_8d_records"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.capa_number}: {self.title} [{self.current_discipline}]"


class CapaVoeRecord(models.Model):
    """
    Verification of Effectiveness (VoE) checkpoint tracking recurrence over 30, 60, and 90-day intervals.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    capa = models.ForeignKey(Capa8dRecord, on_delete=models.CASCADE, related_name="voe_checkpoints")
    milestone = models.CharField(max_length=20, choices=VoeMilestoneChoices.choices)
    target_date = models.DateField()
    verified_date = models.DateField(null=True, blank=True)
    verifier = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    defect_count_in_period = models.PositiveIntegerField(default=0)
    is_effective = models.BooleanField(default=True)
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "capa_voe_records"
        ordering = ["target_date"]

    def __str__(self):
        return f"VoE {self.milestone} for {self.capa.capa_number} (Effective={self.is_effective})"
