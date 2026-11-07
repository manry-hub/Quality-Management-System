from django.contrib import admin
from .models.ipqc_inspection import IpqcInspection, IpqcCavitySample
from .models.telemetry import TelemetrySummary


class IpqcCavitySampleInline(admin.TabularInline):
    model = IpqcCavitySample
    extra = 0
    fields = (
        "shot_number",
        "cavity_number",
        "characteristic_name",
        "measured_value",
        "nominal_value",
        "lsl",
        "usl",
        "is_conforming",
    )


@admin.register(IpqcInspection)
class IpqcInspectionAdmin(admin.ModelAdmin):
    list_display = (
        "machine_code",
        "part",
        "inspection_type",
        "disposition",
        "line_stop_triggered",
        "signed_at",
        "created_at",
    )
    list_filter = ("disposition", "inspection_type", "line_stop_triggered", "machine_code")
    search_fields = ("machine_code", "mes_run_id", "part__part_number")
    readonly_fields = ("created_at", "updated_at", "signature_token")
    inlines = [IpqcCavitySampleInline]


@admin.register(TelemetrySummary)
class TelemetrySummaryAdmin(admin.ModelAdmin):
    list_display = (
        "machine_code",
        "shot_number",
        "cushion_mm",
        "cushion_drift_alert",
        "peak_pressure_bar",
        "fill_time_s",
        "cycle_time_s",
        "created_at",
    )
    list_filter = ("cushion_drift_alert", "machine_code")
    search_fields = ("machine_code", "mes_run_id")
    readonly_fields = ("created_at",)
