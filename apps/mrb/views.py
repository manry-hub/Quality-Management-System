from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from apps.ncr.models.ncr import NonConformanceReport, DispositionType
from .models.mrb import (
    MrbCase,
    MrbStatus,
    MrbRole,
    VoteChoice,
)
from .services import (
    create_mrb_case,
    submit_mrb_vote,
    finalize_mrb_disposition,
)


def mrb_list_view(request):
    """
    Material Review Board (MRB) Deliberation Terminal.
    Coordinates multi-disciplinary engineering reviews with Four-Eyes principle gating.
    """
    status_filter = request.GET.get("status", "")

    mrb_cases = MrbCase.objects.select_related("ncr", "chairperson").prefetch_related("votes__voter").all()
    if status_filter:
        mrb_cases = mrb_cases.filter(status=status_filter)

    total_cases = MrbCase.objects.count()
    in_deliberation_count = MrbCase.objects.filter(status=MrbStatus.IN_DELIBERATION).count()
    approved_count = MrbCase.objects.filter(status=MrbStatus.APPROVED).count()
    rejected_count = MrbCase.objects.filter(status=MrbStatus.REJECTED).count()

    # NCRs eligible for initiating a new MRB case (without an existing MRB case)
    eligible_ncrs = NonConformanceReport.objects.filter(mrb_case__isnull=True).exclude(status="CLOSED")

    context = {
        "title": "Material Review Board (MRB)",
        "subTitle": "Multi-Disciplinary Concession, Rework & Scrap Deliberation Terminal",
        "mrb_cases": mrb_cases,
        "total_cases": total_cases,
        "in_deliberation_count": in_deliberation_count,
        "approved_count": approved_count,
        "rejected_count": rejected_count,
        "status_filter": status_filter,
        "eligible_ncrs": eligible_ncrs,
        "roles": MrbRole.choices,
        "dispositions": DispositionType.choices,
        "vote_choices": VoteChoice.choices,
    }
    return render(request, "mrb/index.html", context)


def mrb_initiate_view(request):
    """
    Initiates an MRB deliberation for a candidate non-conformance.
    """
    if request.method == "POST":
        ncr_id = request.POST.get("ncr_id")
        proposed_disposition = request.POST.get("proposed_disposition", DispositionType.REWORK)
        concession_rationale = request.POST.get("concession_rationale", "").strip()
        customer_doc = request.POST.get("customer_doc", "").strip()

        if not ncr_id:
            messages.error(request, "A valid NCR must be selected.")
            return redirect("mrb:index")

        user = request.user if request.user.is_authenticated else None
        try:
            mrb_case = create_mrb_case(
                ncr_id=ncr_id,
                chairperson=user,
                proposed_disposition=proposed_disposition,
                concession_rationale=concession_rationale,
                customer_doc=customer_doc,
            )
            messages.success(request, f"MRB case initiated for {mrb_case.ncr.ncr_number}.")
        except Exception as e:
            messages.error(request, f"Failed to initiate MRB case: {str(e)}")

    return redirect("mrb:index")


def mrb_vote_view(request, mrb_id):
    """
    Casts a digital 21 CFR Part 11 signature vote on an active MRB deliberation.
    """
    get_object_or_404(MrbCase, id=mrb_id)
    if request.method == "POST":
        voter_role = request.POST.get("voter_role", MrbRole.OPERATIONS_LEAD)
        vote = request.POST.get("vote", VoteChoice.APPROVE)
        comments = request.POST.get("comments", "").strip()

        user = request.user if request.user.is_authenticated else None
        try:
            submit_mrb_vote(
                mrb_case_id=mrb_id,
                voter=user,
                voter_role=voter_role,
                vote=vote,
                comments=comments,
            )
            messages.success(request, f"Digital vote recorded ({voter_role}: {vote}) with SHA-256 seal.")
        except Exception as e:
            messages.error(request, f"Voting failed: {str(e)}")

    return redirect("mrb:index")


def mrb_finalize_view(request, mrb_id):
    """
    Finalizes MRB disposition enforcing the Four-Eyes principle for Use-As-Is concessions.
    """
    get_object_or_404(MrbCase, id=mrb_id)
    if request.method == "POST":
        final_disposition = request.POST.get("final_disposition", DispositionType.REWORK)
        concession_rationale = request.POST.get("concession_rationale", "").strip()
        customer_doc = request.POST.get("customer_doc", "").strip()

        user = request.user if request.user.is_authenticated else None
        try:
            finalized_case = finalize_mrb_disposition(
                mrb_case_id=mrb_id,
                chairperson=user,
                final_disposition=final_disposition,
                concession_rationale=concession_rationale,
                customer_doc=customer_doc,
            )
            messages.success(
                request,
                f"MRB case finalized as {finalized_case.final_disposition} for {finalized_case.ncr.ncr_number}."
            )
        except ValueError as err:
            messages.error(request, f"Four-Eyes Governance Error: {str(err)}")
        except Exception as e:
            messages.error(request, f"Disposition finalization failed: {str(e)}")

    return redirect("mrb:index")
