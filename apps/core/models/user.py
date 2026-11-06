import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models


class DepartmentChoices(models.TextChoices):
    QA = "QA", "Quality Assurance"
    QC = "QC", "Quality Control"
    METROLOGY = "METROLOGY", "Metrology Lab"
    COMPLIANCE = "COMPLIANCE", "Compliance & Audit"
    ENGINEERING = "ENGINEERING", "Quality & Process Engineering"
    TOOLING = "TOOLING", "Tooling & Mold Maintenance"
    OPERATIONS = "OPERATIONS", "Shopfloor Operations"


class User(AbstractUser):
    """
    Custom User Model complying with IATF 16949 and 21 CFR Part 11 requirements.
    Supports physical badge authentication for fast floor-terminal access.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    badge_number = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        help_text="Physical barcode/RFID badge ID for shopfloor terminal authentication."
    )
    department = models.CharField(
        max_length=100,
        choices=DepartmentChoices.choices,
        default=DepartmentChoices.QC,
        db_index=True,
        help_text="Organizational department determining baseline authority."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "users"
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ["username"]

    def __str__(self):
        return f"{self.username} ({self.get_department_display()})"
