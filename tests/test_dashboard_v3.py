"""Regression checks for the five-driver publication payload."""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pipeline"))

from dashboard_v3 import make
from factbase import connect


class DashboardV3Tests(unittest.TestCase):
    def test_publication_contains_only_dashboard(self):
        dist = ROOT / "archive/korea-life-fact-base-v2/dist"
        markup = (dist / "index.html").read_text(encoding="utf-8")
        for name in ("trend.html", "insights.html", "outlook.html", "editorial.js", "editorial.css"):
            self.assertFalse((dist / name).exists(), name)
            self.assertNotIn(name, markup)
        self.assertFalse((dist / "data/editorial.json").exists())
        self.assertIn('id="dashboard"', markup)
        self.assertIn('id="projection"', markup)

    def test_balanced_dashboard_has_independent_drivers(self):
        conn = connect()
        try:
            payload = make(conn)
        finally:
            conn.close()
        self.assertEqual(payload["schema_version"], 3)
        for driver in ("demographic", "life_event", "lifestyle", "home", "spending"):
            self.assertTrue(payload[driver]["source"])
            self.assertTrue(payload[driver]["note"])
        self.assertEqual(payload["lifestyle"]["sleep_minutes"][-1]["year"], 2024)
        self.assertEqual(payload["home"]["tenure"]["owner_share"][-1]["year"], 2020)
        self.assertEqual(payload["spending"]["monthly_won_per_household"]["가전·가정용 기기"][0]["year"], 2019)
        self.assertGreater(payload["official_projection"]["total_households"][-1]["year"], 2025)


if __name__ == "__main__":
    unittest.main()
