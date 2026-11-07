from django.contrib import admin
from .models.vision import VisionInspectionStation, VisionDefectInspection


@admin.register(VisionInspectionStation)
class VisionInspectionStationAdmin(admin.ModelAdmin):
    list_display = ("station_code", "name", "line_cell", "camera_model", "confidence_threshold", "is_online")
    list_filter = ("is_online", "line_cell")
    search_fields = ("station_code", "name")


@admin.register(VisionDefectInspection)
class VisionDefectInspectionAdmin(admin.ModelAdmin):
    list_display = (
        "inspection_timestamp",
        "station",
        "part",
        "shot_number",
        "primary_defect_type",
        "severity",
        "auto_action_taken",
    )
    list_filter = ("primary_defect_type", "severity", "auto_action_taken")
    search_fields = ("part__part_number", "station__station_code")
