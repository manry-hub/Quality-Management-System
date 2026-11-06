from django.contrib import admin
from .models import Part, ResinMaterial


@admin.register(Part)
class PartAdmin(admin.ModelAdmin):
    list_display = (
        "part_number",
        "part_name",
        "drawing_number",
        "drawing_revision",
        "cavity_count",
        "material_code",
        "is_active",
    )
    list_filter = ("is_active", "drawing_revision")
    search_fields = ("part_number", "part_name", "drawing_number", "material_code")


@admin.register(ResinMaterial)
class ResinMaterialAdmin(admin.ModelAdmin):
    list_display = (
        "material_code",
        "material_name",
        "polymer_type",
        "supplier_code",
        "target_moisture_max_pct",
        "target_mfi_nominal",
        "is_active",
    )
    list_filter = ("polymer_type", "is_active", "supplier_code")
    search_fields = ("material_code", "material_name", "supplier_code")
