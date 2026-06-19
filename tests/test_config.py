import os
import unittest
from unittest.mock import patch

from proofgate.config_writer import build_agent_config


class ConfigTests(unittest.TestCase):
    def test_old_engineer_and_reviewer_variables_are_aliases(self):
        values = {
            "BAND_INTAKE_AGENT_ID": "i", "BAND_INTAKE_API_KEY": "ik",
            "BAND_PLANNER_AGENT_ID": "p", "BAND_PLANNER_API_KEY": "pk",
            "BAND_ENGINEER_AGENT_ID": "e", "BAND_ENGINEER_API_KEY": "ek",
            "BAND_ISSUE_ISOLATOR_AGENT_ID": "x", "BAND_ISSUE_ISOLATOR_API_KEY": "xk",
            "BAND_REVIEWER_AGENT_ID": "r", "BAND_REVIEWER_API_KEY": "rk",
        }
        with patch.dict(os.environ, values, clear=True):
            result = build_agent_config()
        self.assertIn("resolution:", result)
        self.assertIn("finalizing:", result)
        self.assertNotIn("tester:", result)
        self.assertNotIn("engineer:", result)
        self.assertNotIn("reviewer:", result)


if __name__ == "__main__":
    unittest.main()
