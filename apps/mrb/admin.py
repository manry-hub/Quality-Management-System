from django.contrib import admin
from .models.mrb import MrbCase, MrbVote


class MrbVoteInline(admin.TabularInline):
    model = MrbVote
    extra = 0
    readonly_fields = ("id", "voter", "voter_role", "vote", "signature_token", "voted_at")


@admin.register(MrbCase)
class MrbCaseAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "ncr",
        "chairperson",
        "proposed_disposition",
        "final_disposition",
        "status",
        "created_at",
    )
    list_filter = ("status", "proposed_disposition", "final_disposition")
    search_fields = ("ncr__ncr_number", "concession_rationale")
    inlines = [MrbVoteInline]
    readonly_fields = ("id", "created_at", "closed_at")


@admin.register(MrbVote)
class MrbVoteAdmin(admin.ModelAdmin):
    list_display = ("id", "mrb_case", "voter", "voter_role", "vote", "voted_at")
    list_filter = ("voter_role", "vote")
    readonly_fields = ("id", "signature_token", "voted_at")
