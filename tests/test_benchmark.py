import unittest
from unittest.mock import patch
from qjai_agent.benchmark import nonnegative_int
from qjai_agent.job import execute_with_metrics


class BenchmarkTests(unittest.TestCase):
    def test_smoke_usage(self):
        with patch.dict("os.environ", {}, clear=True):
            output, usage = execute_with_metrics("smoke", "")
        self.assertIn("OK", output)
        self.assertEqual(usage["total_tokens"], 0)
        self.assertEqual(usage["requests"], 0)

    def test_safe_numeric_values(self):
        for value in (True, -1, "secret", None, 1.5):
            self.assertIsNone(nonnegative_int(value))
        self.assertEqual(nonnegative_int(0), 0)
        self.assertEqual(nonnegative_int(7), 7)
