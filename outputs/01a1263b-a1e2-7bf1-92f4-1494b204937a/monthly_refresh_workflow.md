# Korea Customer/Life Fact Base — Monthly Refresh Workflow

## Schedule

- Frequency: monthly, on the 10th at 09:30 (Asia/Seoul)
- Mode: thread heartbeat
- Notification: only when a material update, collection failure, or a decision request occurs

## Scope and operating rules

1. Start with the `P1 Collection Status` and `Source Registry` sheets in `korea_customer_life_fact_dataset_phase1.xlsx`.
2. Check KOSIS and the cited first-party source for new releases or revisions since the recorded collection date.
3. Keep **Actual** and **Official Projection** as separate observations. Do not fill historical series with forecast values or vice versa.
4. Preserve table ID, source URL, release/collection date, unit, geographic grain, and any transformation in the raw-data and QA fields.
5. When a published table's definition, ID, or classification changes, record the evidence in `Catalog Corrections`; do not silently overwrite the prior mapping.

## Monthly execution sequence

| Step | Action | Output |
|---|---|---|
| 1 | Identify releases/revisions | change log with source and reference date |
| 2 | Download official source data | date-stamped raw extract |
| 3 | Validate unit, period, geography, and status | QA note / exception record |
| 4 | Normalize into Fact Data Long | Actual/Projection-labelled records |
| 5 | Refresh Key Series and Dashboard | updated decision-facing trends |
| 6 | Update status and registry | reproducible catalog history |
| 7 | Notify only if action is needed | concise Korean update |

## Priority queue

1. Correct the official table mappings for H03 (housing tenure) and H02 (living-area bands).
2. Add D05 (dual-income households), L01 (domestic migration), and L02 (migration reasons).
3. Extend remaining P1 lifestyle, home, and spending facts, keeping each source independently auditable.

## Quality gates

- No missing source URL or data identifier for a published observation.
- No mix of actuals and projections in one unlabelled series.
- No aggregation across incompatible units or geographic levels.
- Revision values are retained with an update note rather than silently replaced.
