import logging
from typing import Dict, Any, List
from apps.traceability.models.traceability import TraceabilityNode

logger = logging.getLogger(__name__)


def record_traceability_node(
    node_type: str,
    node_identifier: str,
    parent_identifier: str = None,
    metadata: Dict[str, Any] = None,
) -> TraceabilityNode:
    """
    Ingests or updates a genealogy node in the traceability graph.
    """
    node, created = TraceabilityNode.objects.update_or_create(
        node_identifier=node_identifier,
        defaults={
            "node_type": node_type,
            "parent_identifier": parent_identifier,
            "metadata_snapshot": metadata or {},
        },
    )
    return node


def traverse_backward(start_identifier: str, max_depth: int = 10) -> List[Dict[str, Any]]:
    """
    Backward Genealogy Traversal (Customer / Finished Pallet back to Raw Material).
    Follows parent_identifier chain: PALLET/SHIPMENT -> CARTON -> RUN -> HOPPER -> RESIN_LOT.
    """
    chain = []
    current_id = start_identifier
    depth = 0

    while current_id and depth < max_depth:
        node = TraceabilityNode.objects.filter(node_identifier=current_id).first()
        if not node:
            break

        chain.append({
            "id": node.id,
            "node_type": node.node_type,
            "node_identifier": node.node_identifier,
            "parent_identifier": node.parent_identifier,
            "metadata": node.metadata_snapshot,
            "created_at": node.created_at.isoformat(),
        })

        current_id = node.parent_identifier
        depth += 1

    return chain


def traverse_forward(start_identifier: str, max_depth: int = 10) -> Dict[str, Any]:
    """
    Forward Containment & Impact Traversal (Resin Lot / Mold Tooling down to Pallets & Shipments).
    Computes containment blast radius in < 2 seconds.
    """
    root_node = TraceabilityNode.objects.filter(node_identifier=start_identifier).first()
    if not root_node:
        return {
            "root": None,
            "descendants": [],
            "affected_shipments": [],
            "affected_pallets": [],
            "affected_runs": [],
            "total_impacted_units": 0,
        }

    current_level = [start_identifier]
    all_descendants = []
    affected_shipments = []
    affected_pallets = []
    affected_runs = []
    depth = 0

    while current_level and depth < max_depth:
        children = list(
            TraceabilityNode.objects.filter(parent_identifier__in=current_level)
        )
        if not children:
            break

        next_level = []
        for child in children:
            child_info = {
                "id": child.id,
                "node_type": child.node_type,
                "node_identifier": child.node_identifier,
                "parent_identifier": child.parent_identifier,
                "metadata": child.metadata_snapshot,
                "created_at": child.created_at.isoformat(),
                "depth": depth + 1,
            }
            all_descendants.append(child_info)
            next_level.append(child.node_identifier)

            if child.node_type == "SHIPMENT":
                affected_shipments.append(child_info)
            elif child.node_type == "PALLET":
                affected_pallets.append(child_info)
            elif child.node_type == "RUN":
                affected_runs.append(child_info)

        current_level = next_level
        depth += 1

    return {
        "root": {
            "id": root_node.id,
            "node_type": root_node.node_type,
            "node_identifier": root_node.node_identifier,
            "metadata": root_node.metadata_snapshot,
            "created_at": root_node.created_at.isoformat(),
        },
        "descendants": all_descendants,
        "affected_shipments": affected_shipments,
        "affected_pallets": affected_pallets,
        "affected_runs": affected_runs,
        "total_impacted_units": len(all_descendants),
    }
