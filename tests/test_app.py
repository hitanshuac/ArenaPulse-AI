import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest

from app.deterministic_rules import run_deterministic_crowd_analysis, run_deterministic_translation


class TestArenaPulseTelemetry(unittest.TestCase):

    def test_empty_occupancy_ratio(self):
        """Ensures zero capacity or empty lists are calculated without crashing."""
        result = run_deterministic_crowd_analysis([])
        self.assertEqual(result["decision"], "All monitored stadium zones are operating within acceptable threshold parameters (<80%).")

    def test_density_alarm(self):
        """Validates that occupancy over 80% successfully deploys volunteer diversion triggers."""
        critical_state = [{"zone_id": "Gate B", "current_occupancy": 90, "max_capacity": 100, "associated_gates": "Gate 2"}]
        result = run_deterministic_crowd_analysis(critical_state)
        self.assertIn("Escalation Triggered", result["execution_trace"][0])

    def test_emergency_vocabulary(self):
        """Confirms medical alarm indicators bypass casual routing protocols."""
        result = run_deterministic_translation("Doctor, help! My child is breathing very heavily and is hurt.")
        self.assertEqual(result["urgency_level"], "CRITICAL")
        self.assertEqual(result["detected_intent"], "Medical Emergency Priority")

if __name__ == "__main__":
    unittest.main()
