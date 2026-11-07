import uuid
from django.db import models
from django.conf import settings
from apps.ncr.models.ncr import NonConformanceReport, DispositionType


class MrbStatus(models.TextChoices):
    IN_DELIBERATION = "IN_DELIBERATION", "In Deliberation (Voting Open)"
    APPROVED = "APPROVED", "Approved & Dispositioned"
    REJECTED = "REJECTED", "Rejected (Escalated to Scrap/Quarantine)"


class MrbRole(models.TextChoices):
    QUALITY_MANAGER = "QUALITY_MANAGER", "Quality Assurance Manager"
    CHIEF_ENGINEER = "CHIEF_ENGINEER", "Chief Manufacturing / Process Engineer"
    OPERATIONS_LEAD = "OPERATIONS_LEAD", "Operations / Production Lead"


class VoteChoice(models.TextChoices):
    APPROVE = "APPROVE", "Approve Disposition"
    REJECT = "REJECT", "Reject / Oppose"
    ABSTAIN = "ABSTAIN", "Abstain"


class MrbCase(models.Model):
    """
    Material Review Board (MRB) Deliberation Case (IATF 16949 §8.7).
    Governs multi-role review and Four-Eyes Principle for Concessions (USE_AS_IS).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ncr = models.OneToOneField(
        NonConformanceReport,
        on_delete=models.PROTECT,
        related_name="mrb_case",
    )
    chairperson = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="chaired_mrb_cases",
        help_text="Quality Manager leading the deliberation",
    )
    proposed_disposition = models.CharField(
        max_length=50,
        choices=DispositionType.choices,
        default=DispositionType.REWORK,
    )
    concession_rationale = models.TextField(
        blank=True,
        null=True,
        help_text="Mandatory engineering rationale if USE_AS_IS concession is requested",
    )
    customer_approval_doc = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Customer Concession Approval reference / document link (mandatory for USE_AS_IS)",
    )
    customer_approval_required = models.BooleanField(
        default=False,
        help_text="Flag indicating OEM customer sign-off is mandatory",
    )
    status = models.CharField(
        max_length=50,
        choices=MrbStatus.choices,
        default=MrbStatus.IN_DELIBERATION,
        db_index=True,
    )
    final_disposition = models.CharField(
        max_length=50,
        choices=DispositionType.choices,
        blank=True,
        null=True,
    )
    closed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "mrb_cases"
        ordering = ["-created_at"]

    def __str__(self):
        return f"MRB for {self.ncr.ncr_number} - {self.proposed_disposition} ({self.status})"


class MrbVote(models.Model):
    """
    Individual MRB Member Vote with 21 CFR Part 11 Digital Signature Manifestation.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mrb_case = models.ForeignKey(
        MrbCase,
        on_delete=models.CASCADE,
        related_name="votes",
    )
    voter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="mrb_votes",
    )
    voter_role = models.CharField(
        max_length=50,
        choices=MrbRole.choices,
    )
    vote = models.CharField(
        max_length=20,
        choices=VoteChoice.choices,
    )
    comments = models.TextField(
        blank=True,
        default="",
        help_text="Technical justification or stipulations for vote",
    )
    signature_token = models.CharField(
        max_length=128,
        help_text="Cryptographic SHA-256 signature manifestation",
    )
    voted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "mrb_votes"
        unique_together = [("mrb_case", "voter")]
        ordering = ["voted_at"]

    def __str__(self):
        return f"{self.voter_role}: {self.vote} on {self.mrb_case_id}"
