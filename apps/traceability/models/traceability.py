from django.db import models


class NodeType(models.TextChoices):
    RESIN_LOT = "RESIN_LOT", "Raw Resin Material Lot"
    HOPPER = "HOPPER", "Hopper Drying Batch"
    RUN = "RUN", "IMM Production Run"
    CAVITY = "CAVITY", "Tooling Mold Cavity"
    CARTON = "CARTON", "Packaging Carton"
    PALLET = "PALLET", "Finished Goods Pallet"
    SHIPMENT = "SHIPMENT", "Customer Delivery Order (DO)"


class TraceabilityNode(models.Model):
    """
    Hierarchical Genealogy Node for Forward/Backward Automotive Traceability (IATF 16949 §8.5.2).
    Enables sub-2-second recursive tree traversal across supply chain and manufacturing operations.
    """
    id = models.BigAutoField(primary_key=True)
    node_type = models.CharField(
        max_length=50,
        choices=NodeType.choices,
        db_index=True,
    )
    node_identifier = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="Unique Barcode, Lot Number, Run ID, or Delivery Order Number",
    )
    parent_identifier = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        db_index=True,
        help_text="Identifier of the direct parent entity in the manufacturing chain",
    )
    metadata_snapshot = models.JSONField(
        default=dict,
        blank=True,
        help_text="Associated telemetry, CoA specs, machine parameters, or inspector badge",
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "traceability_nodes"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["parent_identifier"], name="idx_traceability_parent"),
            models.Index(fields=["node_type", "created_at"], name="idx_traceability_type_time"),
        ]

    def __str__(self):
        return f"{self.node_type}: {self.node_identifier} (Parent: {self.parent_identifier or 'None'})"
