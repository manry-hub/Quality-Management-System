from django.contrib import admin
from .models import ControlPlan, ControlPlanItem


class ControlPlanItemInline(admin.TabularInline):
    model = ControlPlanItem
    extra = 1
    fields = (
        "characteristic_name",
        "characteristic_type",
        "special_char_class",
        "target_value",
        "lsl",
        "usl",
        "unit_of_measure",
        "tool_category",
        "sampling_frequency",
    )


@admin.register(ControlPlan)
class ControlPlanAdmin(admin.ModelAdmin):
    list_display = ("part", "revision", "status", "effective_date", "approved_by", "approved_at")
    list_filter = ("status", "revision", "effective_date")
    search_fields = ("part__part_number", "part__part_name", "revision", "fmea_reference")
    inlines = [ControlPlanItemInline]


@admin.register(ControlPlanItem)
class ControlPlanItemAdmin(admin.ModelAdmin):
    list_display = (
        "control_plan",
        "characteristic_name",
        "characteristic_type",
        "special_char_class",
        "target_value",
        "lsl",
        "usl",
        "unit_of_measure",
        "tool_category",
    )
    list_filter = ("characteristic_type", "special_char_class", "tool_category")
    search_fields = ("characteristic_name", "control_plan__part__part_number")
