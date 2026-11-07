from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, AuditTrailEvent, OutboxEvent


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("username", "email", "badge_number", "department", "is_active", "is_staff")
    list_filter = ("department", "is_active", "is_staff")
    search_fields = ("username", "email", "badge_number", "first_name", "last_name")
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Plant Identification & Authority", {"fields": ("badge_number", "department")}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("Plant Identification & Authority", {"fields": ("badge_number", "department")}),
    )


@admin.register(AuditTrailEvent)
class AuditTrailEventAdmin(admin.ModelAdmin):
    list_display = ("id", "timestamp", "action_type", "entity_type", "entity_id", "user", "badge_number", "record_hash")
    list_filter = ("action_type", "entity_type", "timestamp")
    search_fields = ("entity_type", "record_hash", "badge_number", "signature_manifestation")
    readonly_fields = [f.name for f in AuditTrailEvent._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(OutboxEvent)
class OutboxEventAdmin(admin.ModelAdmin):
    list_display = ("id", "event_type", "destination_system", "status", "retry_count", "next_retry_at", "created_at")
    list_filter = ("status", "destination_system", "event_type")
    search_fields = ("event_uuid", "event_type", "destination_system")
    readonly_fields = ("event_uuid", "created_at", "delivered_at")
