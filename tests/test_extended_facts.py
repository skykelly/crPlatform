import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pipeline"))
import extended_facts as ef  # noqa: E402

RAW = ROOT / "data" / "raw" / "2026-10-11"


def staged_rows():
    rows = []
    for table, period, start, dims in ef.SOURCES:
        items = json.loads((RAW / f"{ef.source_key(table, dims, start)}.json").read_text(encoding="utf-8"))
        rows.extend(r for item in items if (r := ef.map_row(table, item, "2026-10-13")) is not None)
    return rows


class ExtendedFactsTests(unittest.TestCase):
    def test_spending_detail_items_are_mapped_and_consistent(self):
        rows = staged_rows()
        facts = {r["fact_id"] for r in rows}
        for fact_id in ("S08", "S09", "S10", "S11", "S12", "S13", "S14", "S15"):
            self.assertIn(fact_id, facts)
        ef.validate(rows)  # S05 = 세부 5개 합, 세부 ≤ 소비지출

    def test_component_mismatch_is_rejected(self):
        rows = staged_rows()
        broken = [dict(r, value_raw="999999") if (r["fact_id"], r["year"]) == ("S08", 2025) else r for r in rows]
        with self.assertRaises(ValueError):
            ef.validate(broken)

    def test_optional_time_use_rows_skip_known_and_missing_values(self):
        base = {"TBL_ID": "DT_1TS202001", "PRD_DE": "2024", "C1": "A0", "C2": "S0", "C3": "C1",
                "ITM_ID": "T10", "ITM_NM": "평균시간", "UNIT_NM": "시간:분"}
        leisure = ef.map_row("DT_1TS202001", {**base, "C4": "S8", "C4_NM": "교제 및 여가활동", "DT": "5:08"}, "x", optional=True)
        self.assertEqual((leisure["fact_id"], leisure["dimension_2_code"]), ("LS09", "S8"))
        self.assertIsNone(ef.map_row("DT_1TS202001", {**base, "C4": "S11", "C4_NM": "수면", "DT": "8:04"}, "x", optional=True))
        self.assertIsNone(ef.map_row("DT_1TS202001", {**base, "C4": "S9", "C4_NM": "기타", "DT": "-"}, "x", optional=True))


if __name__ == "__main__":
    unittest.main()
