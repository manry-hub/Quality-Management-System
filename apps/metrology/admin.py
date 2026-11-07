from django.contrib import admin
from .models import Gauge, GaugeCalibration, MsaStudy


@admin.register(Gauge)
class GaugeAdmin(admin.ModelAdmin):
    list_display = ("device_id", "name", "gauge_type", "location", "next_calibration_due", "status")
    list_filter = ("gauge_type", "status")
    search_fields = ("device_id", "name", "serial_number")


@admin.register(GaugeCalibration)
class GaugeCalibrationAdmin(admin.ModelAdmin):
    list_display = ("gauge", "certificate_number", "calibration_date", "calibrated_by", "as_left_condition")
    list_filter = ("as_left_condition",)
    search_fields = ("certificate_number", "gauge__device_id")


@admin.register(MsaStudy)
class MsaStudyAdmin(admin.ModelAdmin):
    list_display = ("study_number", "gauge", "part", "characteristic_name", "grr_percent", "ndc", "acceptance_status")
    list_filter = ("acceptance_status", "study_type")
    search_fields = ("study_number", "gauge__device_id")
