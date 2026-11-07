from django.contrib import admin
from .models.oqc_inspection import OqcInspection, OqcDefectItem


class OqcDefectItemInline(admin.TabularInline):
    model = OqcDefectItem
    extra = 0
    fields = ("defect_type", "severity", "defect_count", "notes")


@admin.register(OqcInspection)
class OqcInspectionAdmin(admin.ModelAdmin):
    list_display = (
        "pallet_barcode",
        "part",
        "batch_quantity",
        "sample_size",
        "defects_found",
        "coc_number",
        "status",
        "created_at",
    )
    list_filter = ("status", "part")
    search_fields = ("pallet_barcode", "coc_number", "part__part_number")
    readonly_fields = ("created_at", "updated_at", "coc_number", "coc_file_path")
    inlines = [OqcDefectItemInline]


@admin.register(OqcDefectItem)
class OqcDefectItemAdmin(admin.ModelAdmin):
    list_display = ("inspection", "defect_type", "severity", "defect_count", "created_at")
    list_filter = ("severity", "defect_type")
    search_fields = ("inspection__pallet_barcode", "defect_type")
