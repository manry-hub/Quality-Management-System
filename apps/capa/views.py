from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponseBadRequest
from django.contrib.auth import get_user_model
from apps.ncr.models.ncr import NonConformanceReport
from .models.capa import (
    Capa8dRecord,
    CapaDisciplineChoices,
    CapaStatusChoices,
    VoeMilestoneChoices,
)
from .services import (
    create_8d_capa,
    advance_8d_discipline,
    record_voe_checkpoint,
)

User = get_user_model()


def capa_list_view(request):
    status_filter = request.GET.get("status")
    discipline_filter = request.GET.get("discipline")

    queryset = Capa8dRecord.objects.select_related("champion", "leader", "ncr").all()

    if status_filter:
        queryset = queryset.filter(status=status_filter)
    if discipline_filter:
        queryset = queryset.filter(current_discipline=discipline_filter)

    capas = queryset.order_by("-created_at")

    # Metrics
    total_capas = Capa8dRecord.objects.count()
    open_count = Capa8dRecord.objects.filter(status=CapaStatusChoices.OPEN).count()
    in_progress_count = Capa8dRecord.objects.filter(status=CapaStatusChoices.IN_PROGRESS).count()
    under_voe_count = Capa8dRecord.objects.filter(status=CapaStatusChoices.UNDER_VOE).count()
    closed_count = Capa8dRecord.objects.filter(status=CapaStatusChoices.CLOSED).count()

    # Preload users and open NCRs for modal creation
    users = User.objects.filter(is_active=True).order_by("username")
    ncrs = NonConformanceReport.objects.filter(hold_declared=True).order_by("-created_at")[:20]

    context = {
        "capas": capas,
        "total_capas": total_capas,
        "open_count": open_count,
        "in_progress_count": in_progress_count,
        "under_voe_count": under_voe_count,
        "closed_count": closed_count,
        "status_filter": status_filter,
        "discipline_filter": discipline_filter,
        "users": users,
        "ncrs": ncrs,
        "discipline_choices": CapaDisciplineChoices.choices,
        "status_choices": CapaStatusChoices.choices,
    }
    return render(request, "capa/index.html", context)


def capa_create_view(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required.")

    title = request.POST.get("title", "").strip()
    d2_problem = request.POST.get("d2_problem_statement", "").strip()
    champion_id = request.POST.get("champion_id")
    leader_id = request.POST.get("leader_id")
    ncr_id = request.POST.get("ncr_id")

    if not title or not d2_problem or not champion_id or not leader_id:
        messages.error(request, "Please provide Title, Problem Statement, Champion, and Leader.")
        return redirect("capa:index")

    champion = get_object_or_404(User, id=champion_id)
    leader = get_object_or_404(User, id=leader_id)
    ncr = NonConformanceReport.objects.filter(id=ncr_id).first() if ncr_id else None

    # Parse team members
    raw_members = request.POST.get("team_members", "")
    team_members = []
    if raw_members:
        for line in raw_members.splitlines():
            if ":" in line:
                name, role = line.split(":", 1)
                team_members.append({"name": name.strip(), "role": role.strip()})
            elif line.strip():
                team_members.append({"name": line.strip(), "role": "Cross-Functional Team"})

    capa = create_8d_capa(
        title=title,
        champion=champion,
        leader=leader,
        d2_problem_statement=d2_problem,
        team_members=team_members,
        ncr=ncr,
    )

    messages.success(request, f"8D CAPA {capa.capa_number} initialized successfully.")
    return redirect("capa:detail", capa_id=capa.id)


def capa_detail_view(request, capa_id):
    capa = get_object_or_404(
        Capa8dRecord.objects.select_related("champion", "leader", "ncr"),
        id=capa_id,
    )
    voe_checkpoints = list(capa.voe_checkpoints.order_by("target_date"))

    # Ordered disciplines list for the workflow stepper
    disciplines_order = [
        (CapaDisciplineChoices.D1_TEAM, "D1: Team"),
        (CapaDisciplineChoices.D2_PROBLEM, "D2: 5W2H Problem"),
        (CapaDisciplineChoices.D3_CONTAINMENT, "D3: Containment (ICA)"),
        (CapaDisciplineChoices.D4_ROOT_CAUSE, "D4: Root Cause (5-Why & Fishbone)"),
        (CapaDisciplineChoices.D5_PCA_CHOSEN, "D5: Permanent Corrective Action"),
        (CapaDisciplineChoices.D6_PCA_IMPLEMENTED, "D6: Implement & Validate"),
        (CapaDisciplineChoices.D7_PREVENTION, "D7: Prevention (Control Plan/FMEA)"),
        (CapaDisciplineChoices.D8_CLOSED, "D8: Recognition & Closure"),
    ]

    current_idx = 0
    for idx, (code, _) in enumerate(disciplines_order):
        if code == capa.current_discipline:
            current_idx = idx
            break

    # Format 6M Fishbone data
    fishbone = capa.d4_fishbone_data or {}
    fishbone_categories = [
        {"key": "man", "label": "Man (Personnel / Training)", "items": fishbone.get("man", [])},
        {"key": "machine", "label": "Machine (Equipment / Mold / Tooling)", "items": fishbone.get("machine", [])},
        {"key": "material", "label": "Material (Resin / Regrind / Masterbatch)", "items": fishbone.get("material", [])},
        {"key": "method", "label": "Method (Process Parameters / SOP)", "items": fishbone.get("method", [])},
        {"key": "measurement", "label": "Measurement (Gauge / Inspection)", "items": fishbone.get("measurement", [])},
        {"key": "milieu", "label": "Milieu (Environment / Humidity / Temp)", "items": fishbone.get("milieu", [])},
    ]

    context = {
        "capa": capa,
        "voe_checkpoints": voe_checkpoints,
        "disciplines_order": disciplines_order,
        "current_idx": current_idx,
        "fishbone_categories": fishbone_categories,
        "five_why_list": capa.d4_root_cause_5why or [],
        "voe_milestone_choices": VoeMilestoneChoices.choices,
    }
    return render(request, "capa/detail.html", context)


def capa_advance_view(request, capa_id):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required.")

    capa = get_object_or_404(Capa8dRecord, id=capa_id)
    target_discipline = request.POST.get("target_discipline")

    if not target_discipline:
        messages.error(request, "Missing target discipline.")
        return redirect("capa:detail", capa_id=capa.id)

    data = {}
    for key, val in request.POST.items():
        if key not in ("csrfmiddlewaretoken", "target_discipline"):
            data[key] = val

    # Handle 5-Why array if submitted
    five_whys = []
    why_questions = request.POST.getlist("why_question[]")
    why_answers = request.POST.getlist("why_answer[]")
    for q, a in zip(why_questions, why_answers):
        if q.strip() or a.strip():
            five_whys.append({"why": q.strip(), "answer": a.strip()})
    if five_whys:
        data["d4_root_cause_5why"] = five_whys

    # Handle 6M Fishbone if submitted
    fishbone_data = {}
    for cat in ["man", "machine", "material", "method", "measurement", "milieu"]:
        cat_lines = request.POST.get(f"fishbone_{cat}", "").strip()
        if cat_lines:
            fishbone_data[cat] = [line.strip() for line in cat_lines.splitlines() if line.strip()]
        else:
            fishbone_data[cat] = []
    if any(fishbone_data.values()):
        data["d4_fishbone_data"] = fishbone_data

    advance_8d_discipline(capa.id, target_discipline, data)
    messages.success(request, f"Advanced 8D discipline to {target_discipline}.")
    return redirect("capa:detail", capa_id=capa.id)


def capa_voe_submit_view(request, capa_id):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required.")

    capa = get_object_or_404(Capa8dRecord, id=capa_id)
    milestone = request.POST.get("milestone")
    defect_count_str = request.POST.get("defect_count", "0")
    notes = request.POST.get("notes", "").strip()

    try:
        defect_count = int(defect_count_str)
    except ValueError:
        defect_count = 0

    record_voe_checkpoint(
        capa_id=capa.id,
        milestone=milestone,
        defect_count=defect_count,
        notes=notes,
        verifier=request.user if request.user.is_authenticated else None,
    )

    if defect_count == 0:
        messages.success(request, f"VoE {milestone} verified: Zero defect recurrence. Checkpoint PASSED.")
    else:
        messages.warning(
            request,
            f"VoE {milestone} recorded {defect_count} recurrent defects. Corrective action recurrence detected!",
        )

    return redirect("capa:detail", capa_id=capa.id)
