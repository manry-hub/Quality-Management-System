from django.shortcuts import render
from .models.traceability import TraceabilityNode, NodeType
from .services import traverse_backward, traverse_forward


def traceability_index_view(request):
    """
    Interactive Bi-Directional Genealogy & Blast Radius Containment Engine.
    Enables backward trace (finished shipment back to raw polymer lot)
    and forward blast radius analysis (quarantined resin lot down to affected pallets & customer shipments).
    """
    identifier = request.GET.get("identifier", "").strip()
    direction = request.GET.get("direction", "backward")

    results = None
    if identifier:
        if direction == "backward":
            results = {
                "mode": "backward",
                "chain": traverse_backward(identifier),
            }
        else:
            forward_data = traverse_forward(identifier)
            results = {
                "mode": "forward",
                "data": forward_data,
            }

    recent_nodes = TraceabilityNode.objects.order_by("-created_at")[:20]
    total_nodes = TraceabilityNode.objects.count()

    context = {
        "title": "Bi-Directional Lot Genealogy & Blast Radius",
        "subTitle": "IATF 16949 §8.5.2 Complete Supply Chain Pedigree & Quarantine Blast Radius Terminal",
        "identifier": identifier,
        "direction": direction,
        "results": results,
        "recent_nodes": recent_nodes,
        "total_nodes": total_nodes,
        "node_types": NodeType.choices,
    }
    return render(request, "traceability/index.html", context)
