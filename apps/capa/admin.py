from django.contrib import admin
from .models import Capa8dRecord, CapaVoeRecord


@admin.register(Capa8dRecord)
class Capa8dRecordAdmin(admin.ModelAdmin):
    list_display = ("capa_number", "title", "current_discipline", "status", "champion", "leader", "created_at")
    list_filter = ("current_discipline", "status")
    search_fields = ("capa_number", "title", "d2_problem_statement")


@admin.register(CapaVoeRecord)
class CapaVoeRecordAdmin(admin.ModelAdmin):
    list_display = ("capa", "milestone", "target_date", "verified_date", "defect_count_in_period", "is_effective")
    list_filter = ("milestone", "is_effective")
