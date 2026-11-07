import pytest
from django.urls import reverse
from apps.traceability.models.traceability import TraceabilityNode, NodeType


@pytest.fixture
def genealogy_nodes():
    n1 = TraceabilityNode.objects.create(
        node_type=NodeType.RESIN_LOT,
        node_identifier="RESIN-LOT-VIEW-01",
        metadata_snapshot={"polymer": "PA66-GF30"},
    )
    n2 = TraceabilityNode.objects.create(
        node_type=NodeType.RUN,
        node_identifier="RUN-VIEW-01",
        parent_identifier="RESIN-LOT-VIEW-01",
        metadata_snapshot={"machine": "IMM-02"},
    )
    n3 = TraceabilityNode.objects.create(
        node_type=NodeType.PALLET,
        node_identifier="PALLET-VIEW-01",
        parent_identifier="RUN-VIEW-01",
        metadata_snapshot={"qty": 400},
    )
    return n1, n2, n3


@pytest.mark.django_db
class TestTraceabilityViews:
    def test_traceability_index_renders_200(self, client):
        url = reverse("traceability:index")
        response = client.get(url)
        assert response.status_code == 200
        assert "Bi-Directional Lot Genealogy" in response.content.decode()

    def test_traceability_backward_query(self, client, genealogy_nodes):
        url = reverse("traceability:index")
        response = client.get(url, {"identifier": "PALLET-VIEW-01", "direction": "backward"})
        assert response.status_code == 200
        content = response.content.decode()
        assert "PALLET-VIEW-01" in content
        assert "RUN-VIEW-01" in content
        assert "RESIN-LOT-VIEW-01" in content

    def test_traceability_forward_query(self, client, genealogy_nodes):
        url = reverse("traceability:index")
        response = client.get(url, {"identifier": "RESIN-LOT-VIEW-01", "direction": "forward"})
        assert response.status_code == 200
        content = response.content.decode()
        assert "Affected Entities Downstream" in content
        assert "RUN-VIEW-01" in content
        assert "PALLET-VIEW-01" in content
