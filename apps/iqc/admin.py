from django.contrib import admin
from .models.iqc_task import IqcInspectionTask, IqcSample


class IqcSampleInline(admin.TabularInline):
    model = IqcSample
    extra = 0
    fields = (
        "sample_number",
        "bag_pallet_barcode",
        "visual_inspection_passed",
        "moisture_pct",
        "mfi_value",
        "contamination_detected",
    )


@admin.register(IqcInspectionTask)
class IqcInspectionTaskAdmin(admin.ModelAdmin):
    list_display = (
        "lot_number",
        "material",
        "supplier_code",
        "quantity_kg",
        "status",
        "disposition",
        "physical_moisture_pct",
        "physical_mfi_value",
        "created_at",
    )
    list_filter = ("status", "disposition", "material", "supplier_code")
    search_fields = ("lot_number", "wms_event_id", "supplier_code")
    readonly_fields = ("created_at", "updated_at", "wms_event_id")
    inlines = [IqcSampleInline]


@admin.register(IqcSample)
class IqcSampleAdmin(admin.ModelAdmin):
    list_display = (
        "task",
        "sample_number",
        "bag_pallet_barcode",
        "visual_inspection_passed",
        "moisture_pct",
        "mfi_value",
        "contamination_detected",
    )
    list_filter = ("visual_inspection_passed", "contamination_detected")
    search_fields = ("bag_pallet_barcode", "task__lot_number")
