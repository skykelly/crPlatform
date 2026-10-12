import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipeline"))
import official_tables as ot  # noqa: E402


def spec(**kw):
    base = {"fact": "H02", "tbl": "DT_1LC0030", "org": "101", "driver": "Home", "topic": "평형", "title": "t",
            "prd": "Y", "start": 2020, "objL": ["00", "ALL", "ALL"], "geo": 0, "itm": "T11"}
    base.update(kw)
    return base


def row(**kw):
    base = {"TBL_ID": "DT_1LC0030", "PRD_DE": "2024", "C1": "00", "C1_NM": "전국", "C2": "20", "C2_NM": "청년가구",
            "C3": "11", "C3_NM": "40㎡이하", "ITM_ID": "T11", "ITM_NM": "가구수", "UNIT_NM": "가구", "DT": "1,234"}
    base.update(kw)
    return base


class OfficialTablesTests(unittest.TestCase):
    def test_geography_dropped_and_dimensions_mapped(self):
        rows = ot.map_rows(spec(), [row(), row(C3="12", C3_NM="40㎡초과 ~ 60㎡이하", DT="-")], "2026-10-13")
        self.assertEqual(len(rows), 1)  # '-'는 건너뜀
        r = rows[0]
        self.assertEqual((r["geography_code"], r["dimension_2_code"], r["dimension_3_code"], r["value_raw"]), ("00", "20", "11", "1234"))

    def test_non_national_geography_rejected(self):
        with self.assertRaises(ValueError):
            ot.map_rows(spec(), [row(C1="11")], "x")

    def test_keep_items_and_monthly_survey(self):
        s = spec(tbl="DT_1DE7100S", prd="M", objL=["ALL"], geo=None, itm="ALL", keep_items=["T02"])
        items = [{"TBL_ID": "DT_1DE7100S", "PRD_DE": "202408", "C1": "4", "C1_NM": "재택 및 원격근무제", "ITM_ID": i, "ITM_NM": i, "DT": "15.9"} for i in ("T01", "T02")]
        rows = ot.map_rows(s, items, "x")
        self.assertEqual([(r["year"], r["measure_code"]) for r in rows], [(2024, "T02")])
        with self.assertRaises(ValueError):
            ot.map_rows(s, items + [dict(items[1], PRD_DE="202403")], "x")

    def test_spec_tables_are_unique_and_complete(self):
        tables = ot.load_spec()
        self.assertEqual(len({t["tbl"] for t in tables}), len(tables))
        for t in tables:
            for key in ("fact", "tbl", "org", "prd", "start", "objL", "itm"):
                self.assertIn(key, t)
            if t.get("geo") is not None:
                self.assertLess(t["geo"], len(t["objL"]))


if __name__ == "__main__":
    unittest.main()
