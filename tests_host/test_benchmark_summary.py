import unittest
from scripts.benchmark import summarize


class SummaryTests(unittest.TestCase):
    def test_small_sample_has_no_p95(self):
        s = summarize([{"status": "succeeded", "business_wall_ms": 10},
                       {"status": "succeeded", "business_wall_ms": 20}])
        self.assertEqual(s["metrics"]["business_wall_ms"]["mean"], 15)
        self.assertIsNone(s["metrics"]["business_wall_ms"]["p95"])
        self.assertIsNone(s["usage_totals"]["total_tokens"])

    def test_nearest_rank(self):
        s = summarize([{"status": "succeeded", "business_wall_ms": i,
                        "usage": {"total_tokens": 1}} for i in range(1, 21)])
        self.assertEqual(s["metrics"]["business_wall_ms"]["p95"], 19)
        self.assertEqual(s["usage_totals"]["total_tokens"], 20)

    def test_failure_not_counted_as_zero(self):
        s = summarize([{"status": "failed", "business_wall_ms": 1},
                       {"status": "succeeded", "business_wall_ms": 50,
                        "usage": {"total_tokens": 4}}])
        self.assertEqual(s["failed"], 1)
        self.assertEqual(s["metrics"]["business_wall_ms"]["mean"], 50)
        self.assertIsNone(s["usage_totals"]["total_tokens"])
