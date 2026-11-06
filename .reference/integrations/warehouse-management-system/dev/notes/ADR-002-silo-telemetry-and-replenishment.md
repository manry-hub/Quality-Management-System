# ADR-002: Bulk Resin Silo Ultrasonic/Radar Level Telemetry and Automated Replenishment

**Status:** `ACCEPTED`  
**Date:** `2026-10-30`  
**Decision Owners:** `Core Architecture Team`  
**Supersedes:** `None`  
**Superseded By:** `None`

---

## Context

In discrete plastic injection molding facilities, high-volume thermoplastic polymers (such as Polypropylene Homopolymer and High-Impact Polystyrene) are delivered via bulk pneumatic tanker trucks and stored in outdoor vertical industrial silos (20,000 kg – 60,000 kg capacity) rather than palletized 25 kg bags. Running out of bulk resin unexpectedly halts production lines, while overfilling a silo during tanker discharge causes catastrophic filter blockage and polymer loss.

To automate bulk resin inventory tracking:
1. Industrial ultrasonic and 80 GHz continuous wave radar level transmitters measure the ullage (empty distance from transmitter horn to the polymer bed surface).
2. The warehouse management system must ingest continuous or periodic distance readings over secure HTTP webhooks / IoT gateways.
3. The system must convert non-linear geometric readings (conical hopper bottom + cylindrical vertical body) into cubic meters and kilograms using material bulk density.
4. When silo mass drops below economic reorder thresholds, the system must trigger automated purchase requisitions while preventing duplicate requisition spamming.

## Decision

1. **Physical Silo Model & Bin Integration**:
   - Model silos as first-class domain entities (`silos`) tightly linked to a designated `WarehouseBin` in a `SILO` zone area.
   - Store exact physical dimensions: cylinder diameter, total height, conical hopper height, sensor deadband offset, and item bulk density ($kg/m^3$).
2. **Volumetric Calculation Service (`SiloGeometryService`)**:
   - Implement analytical geometry combining the conical hopper section ($V_{cone} = \frac{1}{3}\pi r^2 h$) and the vertical cylindrical barrel ($V_{cyl} = \pi r^2 h$).
   - Derive instantaneous stored mass ($M = V \times \rho_{bulk}$) and fill percentage.
3. **Telemetry Ingestion Gateway (`SiloTelemetryService` & API Endpoint)**:
   - Provide an authenticated endpoint `POST /api/v1/telemetry/silo-reading` accepting sensor distance ($m$), transmitter type, and temperature.
   - Persist time-series telemetry in `silo_telemetry_readings` and atomically update the current state on the `silos` record.
4. **Automated Purchase Requisition (PR) Guard**:
   - When calculated stored weight $\le$ `reorder_threshold_kg`, automatically generate a `PurchaseRequisition` in `DRAFT` status.
   - Enforce idempotency: If an active (non-fulfilled, non-cancelled) requisition or open delivery order already exists for that silo and SKU, prevent duplicate requisitions.
5. **Filament Industrial Visualizer**:
   - Embed high-contrast vertical cylinder level gauges on Filament adhering to [`DESIGN.md`](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/DESIGN.md) dark theme tokens (`#09090b` canvas, `#18181b` card fills, dynamic fill color status).

## Considered Options

| Option | Summary | Decision |
| :--- | :--- | :--- |
| **Linear Ullage Interpolation** | Approximate silo volume as pure cylinder ignoring bottom cone. | **Rejected**: Errors exceed 15–20% near the conical hopper base, causing premature false alarms or dry runs. |
| **Separate IoT Microservice** | Host a standalone Python/Node IoT telemetry microservice with its own database. | **Rejected**: Unnecessary architectural complexity. Laravel with MariaDB InnoDB easily handles telemetry streams and provides atomic consistency with WMS inventory and procurement. |
| **First-Class Domain Silo Engine** | Native Laravel domain services (`SiloGeometryService`, `SiloTelemetryService`) with API endpoint and Filament visualization. | **Selected**: Direct integration with items, bins, purchase requisitions, and Filament dashboards. |

## Consequences

### Positive
- Real-time continuous visibility of bulk resin stocks without manual dip-stick climbing.
- Accurate mass conversion accounting for conical hopper geometry and resin bulk densities.
- Elimination of stockout halts through automated, de-duplicated procurement requisitions.

### Negative or Trade-offs
- Granular materials form repose angles (cones/craters) during fill/discharge; continuous radar level sensors measure center ullage which introduces a $\pm 2-3\%$ natural variance compared to static weigh cells.

### Follow-up
- Implement `SiloGeometryService` with full conical math unit tests.
- Implement API controller and automated purchase requisition generator.
- Build Filament gauge visualizer and simulation CLI.

## References

- [PRD.md](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/docs/dev/PRD.md) (Post-MVP Priority #2)
- [DESIGN.md](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/DESIGN.md)
