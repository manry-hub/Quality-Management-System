import pytest
from apps.traceability.models.traceability import NodeType
from apps.traceability.services import (
    record_traceability_node,
    traverse_backward,
    traverse_forward,
)


@pytest.fixture
def genealogy_chain(db):
    # 1. Resin raw lot
    record_traceability_node(
        node_type=NodeType.RESIN_LOT,
        node_identifier="LOT-PP-202610-01",
        parent_identifier=None,
        metadata={"supplier": "VEND-LOTTE", "moisture_pct": 0.012, "mfi": 18.2},
    )
    # 2. Hopper dryer
    record_traceability_node(
        node_type=NodeType.HOPPER,
        node_identifier="HOPPER-DRYER-01",
        parent_identifier="LOT-PP-202610-01",
        metadata={"dryer_temp_c": 80.0, "dew_point_c": -40.0},
    )
    # 3. Machine production run
    record_traceability_node(
        node_type=NodeType.RUN,
        node_identifier="IMM-04-RUN-2041",
        parent_identifier="HOPPER-DRYER-01",
        metadata={"machine": "IMM-04", "mold": "MOLD-BUMP-2C", "fai_token": "fai_tok_9918"},
    )
    # 4. Packaging carton
    record_traceability_node(
        node_type=NodeType.CARTON,
        node_identifier="CARTON-2026-0811",
        parent_identifier="IMM-04-RUN-2041",
        metadata={"qty": 50, "operator_badge": "OP-441"},
    )
    # 5. Finished goods pallet
    record_traceability_node(
        node_type=NodeType.PALLET,
        node_identifier="PALLET-2026-0042",
        parent_identifier="CARTON-2026-0811",
        metadata={"coc_number": "COC-2026-0042", "c_zero_inspected": True},
    )
    # 6. Customer Delivery Order shipment
    record_traceability_node(
        node_type=NodeType.SHIPMENT,
        node_identifier="DO-CUST-9901",
        parent_identifier="PALLET-2026-0042",
        metadata={"customer": "OEM-AUTOMOTIVE-NORTH", "carrier": "DHL-FREIGHT"},
    )


@pytest.mark.django_db
class TestTraceabilityGenealogy:
    def test_traverse_backward_from_shipment_to_raw_resin(self, genealogy_chain):
        chain = traverse_backward(start_identifier="DO-CUST-9901")

        assert len(chain) == 6
        identifiers = [item["node_identifier"] for item in chain]
        expected_order = [
            "DO-CUST-9901",
            "PALLET-2026-0042",
            "CARTON-2026-0811",
            "IMM-04-RUN-2041",
            "HOPPER-DRYER-01",
            "LOT-PP-202610-01",
        ]
        assert identifiers == expected_order
        assert chain[-1]["metadata"]["supplier"] == "VEND-LOTTE"

    def test_traverse_forward_blast_radius_from_contaminated_lot(self, genealogy_chain):
        impact = traverse_forward(start_identifier="LOT-PP-202610-01")

        assert impact["root"]["node_identifier"] == "LOT-PP-202610-01"
        assert impact["total_impacted_units"] == 5

        # Verify affected pallet and shipment identified for containment
        affected_pallet_ids = [p["node_identifier"] for p in impact["affected_pallets"]]
        assert "PALLET-2026-0042" in affected_pallet_ids

        affected_shipment_ids = [s["node_identifier"] for s in impact["affected_shipments"]]
        assert "DO-CUST-9901" in affected_shipment_ids

    def test_traverse_unknown_identifier_returns_empty(self, db):
        backward = traverse_backward(start_identifier="NON-EXISTENT-BARCODE")
        assert backward == []

        forward = traverse_forward(start_identifier="NON-EXISTENT-LOT")
        assert forward["root"] is None
        assert forward["total_impacted_units"] == 0
