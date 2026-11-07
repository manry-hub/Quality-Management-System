from django.db import models


class TelemetrySummary(models.Model):
    id = models.BigAutoField(primary_key=True)
    machine_code = models.CharField(
        max_length=50,
        db_index=True,
        help_text="Machine identifier (e.g. IMM-01)",
    )
    mold_code = models.CharField(max_length=100)
    mes_run_id = models.CharField(max_length=100, db_index=True)
    shot_number = models.PositiveIntegerField()
    cushion_mm = models.DecimalField(
        max_digits=6,
        decimal_places=3,
        help_text="End-of-holding screw cushion position",
    )
    peak_pressure_bar = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        help_text="Peak plastic injection pressure in bar",
    )
    fill_time_s = models.DecimalField(
        max_digits=6,
        decimal_places=3,
        help_text="First-stage injection filling time in seconds",
    )
    cycle_time_s = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        help_text="Total cycle duration",
    )
    cushion_nominal_mm = models.DecimalField(
        max_digits=6,
        decimal_places=3,
        default=5.000,
    )
    cushion_drift_alert = models.BooleanField(
        default=False,
        help_text="True if deviation exceeds +/- 0.5mm window",
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "ipqc_telemetry_summaries"
        ordering = ["-created_at"]
        verbose_name = "Telemetry Summary"
        verbose_name_plural = "Telemetry Summaries"

    def __str__(self):
        return (
            f"Shot #{self.shot_number} on {self.machine_code}: "
            f"Cushion={self.cushion_mm}mm, Pressure={self.peak_pressure_bar}bar"
        )
