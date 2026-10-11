import sqlite3
import tempfile
import unittest
from pathlib import Path

from pipeline import factbase


class PipelineTests(unittest.TestCase):
    def test_api_mapping_keeps_actual_and_projection_separate(self):
        base = {"TBL_ID": "DT_1PL1502", "PRD_SE": "Y", "PRD_DE": "2025", "C1": "00", "C1_NM": "전국", "C2": "000", "C2_NM": "합계", "ITM_ID": "T00", "ITM_NM": "1인가구", "DT": "8,244,308", "UNIT_NM": "가구"}
        actual = factbase.from_api("DT_1PL1502", base, "2026-10-11")
        self.assertEqual((actual["fact_id"], actual["actual_projection"], actual["value_raw"]), ("D01", "Actual", "8244308"))
        projected = factbase.from_api("DT_1BZ0506", {**base, "TBL_ID": "DT_1BZ0506", "PRD_DE": "2052", "ITM_ID": "T02", "DT": "9,619,733"}, "2026-10-11")
        self.assertEqual((projected["fact_id"], projected["actual_projection"]), ("D02", "Official Projection"))
        with self.assertRaises(ValueError):
            factbase.from_api("DT_1PL1502", {**base, "C4": "unexpected"}, "2026-10-11")

    def test_revisions_and_missing_markers_are_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            conn = factbase.connect(Path(directory) / "test.sqlite")
            row = dict(fact_id="D01", driver="Demographic", topic="1인가구", dataset_id="DT_1PL1502", actual_projection="Actual", year=2025,
                       geography_code="00", geography_name="전국", dimension_2_code="000", dimension_2_name="합계", dimension_3_code="", dimension_3_name="",
                       measure_code="T00", measure_name="1인가구", value_raw="X", unit="가구", source_url="https://kosis.kr/test", retrieved_at="2026-10-10")
            with conn:
                self.assertTrue(factbase.insert_row(conn, row))
                self.assertFalse(factbase.insert_row(conn, row, revisions=True))
                self.assertTrue(factbase.insert_row(conn, {**row, "value_raw": "8244308", "retrieved_at": "2026-10-11"}, revisions=True))
            self.assertEqual(tuple(conn.execute("SELECT old_value,new_value FROM revisions").fetchone()), ("X", "8244308"))
            self.assertEqual(conn.execute("SELECT count(*) FROM observations").fetchone()[0], 1)
            with self.assertRaises(ValueError):
                with conn:
                    projection = {**row, "dataset_id": "DT_1BZ0506", "fact_id": "D02", "actual_projection": "Official Projection"}
                    factbase.insert_row(conn, projection)
                    factbase.insert_row(conn, {**projection, "value_raw": "999"}, revisions=True)
            conn.close()


if __name__ == "__main__":
    unittest.main()
