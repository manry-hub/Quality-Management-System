from django.contrib import admin
from .models.sqa import Supplier, CertificateOfAnalysis, SupplierScorecard


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "country", "tier", "status", "iso_certification")
    list_filter = ("status", "tier", "country")
    search_fields = ("code", "name", "contact_email")


@admin.register(CertificateOfAnalysis)
class CertificateOfAnalysisAdmin(admin.ModelAdmin):
    list_display = ("coa_number", "supplier", "material", "lot_number", "compliance_score", "status")
    list_filter = ("status", "supplier")
    search_fields = ("coa_number", "lot_number")


@admin.register(SupplierScorecard)
class SupplierScorecardAdmin(admin.ModelAdmin):
    list_display = ("supplier", "period_label", "grade", "ppm_defect_rate", "on_time_delivery_pct")
    list_filter = ("grade", "period_label")
    search_fields = ("supplier__code", "period_label")
