import json
import unittest
from datetime import date
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1] / "sites/korea-life-fact-base-v2/dist"
EDITORIAL = json.loads((ROOT / "data/editorial.json").read_text(encoding="utf-8"))


class EditorialContentTests(unittest.TestCase):
    def test_every_driver_has_a_trend(self):
        self.assertEqual(set(EDITORIAL["drivers"]), {d for trend in EDITORIAL["trends"] for d in trend["drivers"]})

    def test_source_links_and_dates(self):
        as_of = date.fromisoformat(EDITORIAL["as_of"])
        for trend in EDITORIAL["trends"]:
            self.assertLessEqual(date.fromisoformat(trend["date"]), as_of)
            self.assertIn(urlparse(trend["url"]).scheme, {"https"})
            for field in ("fact", "life", "limit", "metric", "source"):
                self.assertTrue(trend[field], (trend["id"], field))

    def test_insights_refer_to_source_cards(self):
        trend_ids = {trend["id"] for trend in EDITORIAL["trends"]}
        for insight in EDITORIAL["insights"]:
            self.assertTrue(insight["trends"])
            self.assertTrue(set(insight["trends"]) <= trend_ids)

    def test_navigation_on_all_pages(self):
        for page in ("index", "trend", "insights", "outlook"):
            markup = (ROOT / f"{page}.html").read_text(encoding="utf-8")
            with self.subTest(page=page):
                self.assertIn('aria-label="주요 페이지"', markup)
                for destination in ("trend.html", "insights.html", "outlook.html"):
                    self.assertIn(destination, markup)


if __name__ == "__main__":
    unittest.main()
