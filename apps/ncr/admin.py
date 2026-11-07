from django.contrib import admin
from .models.ncr import NonConformanceReport


@admin.register(NonConformanceReport)
class NonConformanceReportAdmin(admin.ModelAdmin):
    list_display = (
        "ncr_number",
        "source_domain",
        "severity",
        "target_type",
        "target_identifier",
        "status",
        "hold_declared",
        "created_at",
    )
    list_filter = ("source_domain", "severity", "status", "hold_declared", "target_type")
    search_fields = ("ncr_number", "target_identifier", "defect_description")
    readonly_fields = ("id", "created_at", "updated_at")
