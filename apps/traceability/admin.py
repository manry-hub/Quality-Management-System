from django.contrib import admin
from .models.traceability import TraceabilityNode


@admin.register(TraceabilityNode)
class TraceabilityNodeAdmin(admin.ModelAdmin):
    list_display = ("id", "node_type", "node_identifier", "parent_identifier", "created_at")
    list_filter = ("node_type",)
    search_fields = ("node_identifier", "parent_identifier")
    readonly_fields = ("id", "created_at")
