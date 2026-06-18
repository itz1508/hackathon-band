import unittest

from proofgate.core import run_demo


class ProofGateDemoTests(unittest.TestCase):
    def test_demo_produces_safe_proof_packet(self):
        transcript, proof = run_demo()

        self.assertEqual(transcript["routing_model"], "@mention")
        self.assertTrue(proof["safe_to_apply"])
        self.assertEqual(proof["human_action"], "approve_or_reject")
        self.assertIn("what_wrong", proof)
        self.assertIn("why_it_matters", proof)
        self.assertIn("how_to_fix", proof)
        self.assertIn("demo_repo/auth.py", proof["scoped_files"])

    def test_all_required_agents_speak(self):
        transcript, _ = run_demo()
        senders = {message["sender"] for message in transcript["messages"]}

        self.assertIn("@Planner", senders)
        self.assertIn("@Engineer", senders)
        self.assertIn("@Tester", senders)
        self.assertIn("@Reviewer", senders)

    def test_proof_packet_contains_simulated_diff_and_validation(self):
        _, proof = run_demo()

        self.assertIn("--- demo_repo/auth.py.before", proof["simulated_diff"])
        self.assertTrue(proof["validation_summary"]["all_tests_passed"])
        self.assertTrue(proof["validation_summary"]["scope_ok"])


if __name__ == "__main__":
    unittest.main()

