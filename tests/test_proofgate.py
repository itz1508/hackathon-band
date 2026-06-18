import unittest
from http.client import HTTPConnection
from threading import Thread

from proofgate.core import run_demo
from proofgate.band_adapter import describe_band_tool_contracts, describe_live_handoffs
from proofgate.config_writer import build_agent_config
from proofgate.remote_agent import ROLE_NOTES, main as remote_agent_main
from proofgate.server import ProofGateRequestHandler, ThreadingHTTPServer


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

        self.assertIn("@itz1508/planner", senders)
        self.assertIn("@itz1508/engineer", senders)
        self.assertIn("@itz1508/tester", senders)
        self.assertIn("@itz1508/reviewer", senders)

    def test_proof_packet_contains_simulated_diff_and_validation(self):
        _, proof = run_demo()

        self.assertIn("--- demo_repo/auth.py.before", proof["simulated_diff"])
        self.assertTrue(proof["validation_summary"]["all_tests_passed"])
        self.assertTrue(proof["validation_summary"]["scope_ok"])

    def test_band_tool_contract_includes_required_handoff_service(self):
        services = {contract["service"] for contract in describe_band_tool_contracts()}

        self.assertIn("send_direct_message_service", services)
        self.assertIn("add_participant_service", services)
        self.assertIn("list_available_participants_service", services)

    def test_live_handoffs_use_direct_messages(self):
        handoffs = describe_live_handoffs()

        self.assertEqual(handoffs[0]["from"], "@itz1508")
        self.assertEqual(handoffs[-1]["to"], "@itz1508")
        self.assertTrue(all(handoff["service"] == "send_direct_message_service" for handoff in handoffs))

    def test_server_exposes_proof_packet_endpoint(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), ProofGateRequestHandler)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            connection = HTTPConnection("127.0.0.1", server.server_port, timeout=5)
            connection.request("GET", "/api/proof-packet")
            response = connection.getresponse()
            body = response.read().decode("utf-8")
            self.assertEqual(response.status, 200)
            self.assertIn("safe_to_apply", body)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

    def test_agent_config_writer_uses_all_roles(self):
        import os
        from unittest.mock import patch

        env = {
            "BAND_PLANNER_AGENT_ID": "planner-id",
            "BAND_PLANNER_API_KEY": "planner-key",
            "BAND_ENGINEER_AGENT_ID": "engineer-id",
            "BAND_ENGINEER_API_KEY": "engineer-key",
            "BAND_TESTER_AGENT_ID": "tester-id",
            "BAND_TESTER_API_KEY": "tester-key",
            "BAND_REVIEWER_AGENT_ID": "reviewer-id",
            "BAND_REVIEWER_API_KEY": "reviewer-key",
        }
        with patch.dict(os.environ, env, clear=True):
            config = build_agent_config()

        self.assertIn("planner:", config)
        self.assertIn('agent_id: "planner-id"', config)
        self.assertIn("engineer:", config)
        self.assertIn("tester:", config)
        self.assertIn("reviewer:", config)

    def test_remote_agent_roles_are_defined(self):
        self.assertEqual(set(ROLE_NOTES), {"planner", "engineer", "tester", "reviewer"})

    def test_remote_agent_cli_uses_defined_roles(self):
        self.assertIsNotNone(remote_agent_main)


if __name__ == "__main__":
    unittest.main()
