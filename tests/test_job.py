import json
import os
import subprocess
import sys
import unittest
from unittest.mock import patch

from qjai_agent.job import execute


class JobTests(unittest.TestCase):
    def test_smoke_without_model_credentials(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertIn("OK", execute("smoke", ""))

    def test_invalid_mode(self):
        with self.assertRaises(ValueError):
            execute("invalid", "")

    def test_live_requires_credentials(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError):
                execute("live", "")

    def test_cli_contract(self):
        env = dict(os.environ, AGENT_MODE="smoke", RUN_ID="test-run", BUSINESS_DATE="2026-11-27")
        proc = subprocess.run([sys.executable, "-m", "qjai_agent"], env=env, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0)
        record = json.loads(proc.stdout)
        self.assertEqual(record["run_id"], "test-run")
        self.assertEqual(record["status"], "succeeded")
        self.assertEqual(record["business_date"], "2026-11-27")

    def test_failed_cli(self):
        proc = subprocess.run([sys.executable, "-m", "qjai_agent"], env=dict(os.environ, AGENT_MODE="invalid"), capture_output=True, text=True)
        self.assertNotEqual(proc.returncode, 0)
        self.assertEqual(json.loads(proc.stdout)["status"], "failed")


if __name__ == "__main__":
    unittest.main()
