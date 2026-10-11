# Korea Customer/Life Fact Base — Monthly Refresh Workflow

## Schedule

- Frequency: monthly, on the 10th at 09:30 (Asia/Seoul)
- Mode: GitHub Actions (`.github/workflows/factbase-refresh.yml`), plus manual dispatch
- Prerequisite: repository secret `KOSIS_API_KEY`
- Publication: validated changes are committed to `main`; the published dashboard reads the public JSON on the next page load

## Scope and operating rules

1. Start with the `P1 Collection Status` and `Source Registry` sheets in `korea_customer_life_fact_dataset_phase1.xlsx`.
2. The automated collector checks the eight KOSIS tables already normalized in the DB. Other catalog sources remain a manual research queue.
3. Keep **Actual** and **Official Projection** as separate observations. Do not fill historical series with forecast values or vice versa.
4. Preserve table ID, source URL, release/collection date, unit, geographic grain, and any transformation in the raw-data and QA fields.
5. When a published table's definition, ID, classification or forecast vintage changes, stop the automated publication and review the mapping before rerunning.

## Monthly execution sequence

| Step | Action | Output |
|---|---|---|
| 1 | Query the official KOSIS API | eight table responses; key stays in GitHub Secrets |
| 2 | Validate table, year, national geography, dimensions, duplicates and status | fail before publication if a rule breaks |
| 3 | Apply observations and preserve revisions | `data/factbase.sqlite` and `revisions` table |
| 4 | Save changed source responses | `data/raw/YYYY-MM-DD/` |
| 5 | Build the dashboard feed | `sites/korea-life-fact-base/dist/data/dashboard.json` |
| 6 | Commit only verified changes | public GitHub `main`; website reads them directly |

## Priority queue

1. Correct the official table mappings for H03 (housing tenure) and H02 (living-area bands).
2. Add D05 (dual-income households), L01 (domestic migration), and L02 (migration reasons).
3. Extend remaining P1 lifestyle, home, and spending facts, keeping each source independently auditable.

## Quality gates

- No missing source URL or data identifier for a published observation.
- No mix of actuals and projections in one unlabelled series.
- No aggregation across incompatible units or geographic levels.
- Revision values are retained with an update note rather than silently replaced.
- Official Projection values that differ from the stored 2022-base vintage are rejected until the new vintage is identified.
- Missing API credentials or an API error fails the run and leaves the published DB and web feed unchanged.
