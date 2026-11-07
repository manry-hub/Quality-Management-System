from django.contrib import admin
from .models import SpcControlChart, SpcSubgroup


@admin.register(SpcControlChart)
class SpcControlChartAdmin(admin.ModelAdmin):
    list_display = ("name", "part", "characteristic_name", "chart_type", "nominal", "usl", "lsl", "cpk", "is_active")
    list_filter = ("chart_type", "is_active")
    search_fields = ("name", "characteristic_name", "part__part_number")


@admin.register(SpcSubgroup)
class SpcSubgroupAdmin(admin.ModelAdmin):
    list_display = ("chart", "subgroup_number", "sample_size", "mean", "range_val", "std_dev", "created_at")
    list_filter = ("chart",)
    search_fields = ("chart__name",)
