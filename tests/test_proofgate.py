import unittest
from dataclasses import dataclass
from http.client import HTTPConnection
from threading import Thread
from types import SimpleNamespace

from proofgate.core import run_demo
from proofgate.band_adapter import describe_band_tool_contracts, describe_live_handoffs
from proofgate.config_writer import build_agent_config
from proofgate.remote_agent import (
    ProofGateDirectAdapter,
    ROLE_NOTES,
    ROLE_TARGETS,
    ROLE_TARGET_LABELS,
    main as remote_agent_main,
)
from proofgate.server import ProofGateRequestHandler, ThreadingHTTPServer


@dataclass(frozen=True)
class FakeMessage:
    content: str
    sender_name: str = "@itz1508"

    def format_for_llm(self) -> str:
        return f"[{self.sender_name}]: {self.content}"


class FakeCompletions:
    def __init__(self, content, exc=None):
        self.content = content
        self.exc = exc
        self.calls = []

    async def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.exc:
            raise self.exc
        message = SimpleNamespace(content=self.content)
        choice = SimpleNamespace(message=message)
        return SimpleNamespace(choices=[choice])


class FakeTools:
    def __init__(self):
        self.messages_sent = []

    async def send_message(self, content, mentions=None):
        self.messages_sent.append({"content": content, "mentions": mentions or []})


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
            "BAND_INTAKE_AGENT_ID": "intake-id",
            "BAND_INTAKE_API_KEY": "intake-key",
            "BAND_PLANNER_AGENT_ID": "planner-id",
            "BAND_PLANNER_API_KEY": "planner-key",
            "BAND_ENGINEER_AGENT_ID": "engineer-id",
            "BAND_ENGINEER_API_KEY": "engineer-key",
            "BAND_TESTER_AGENT_ID": "tester-id",
            "BAND_TESTER_API_KEY": "tester-key",
            "BAND_REVIEWER_AGENT_ID": "reviewer-id",
            "BAND_REVIEWER_API_KEY": "reviewer-key",
            "BAND_ISSUE_ISOLATOR_AGENT_ID": "issue-isolator-id",
            "BAND_ISSUE_ISOLATOR_API_KEY": "issue-isolator-key",
        }
        with patch.dict(os.environ, env, clear=True):
            config = build_agent_config()

        self.assertIn("planner:", config)
        self.assertIn("intake:", config)
        self.assertIn('agent_id: "planner-id"', config)
        self.assertIn("engineer:", config)
        self.assertIn("tester:", config)
        self.assertIn("reviewer:", config)
        self.assertIn("issue-isolator:", config)

    def test_agent_config_writer_skips_absent_optional_roles(self):
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
        self.assertIn("engineer:", config)
        self.assertIn("tester:", config)
        self.assertIn("reviewer:", config)
        self.assertNotIn("intake:", config)
        self.assertNotIn("issue-isolator:", config)

    def test_agent_config_writer_rejects_partial_optional_role(self):
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
            "BAND_ISSUE_ISOLATOR_AGENT_ID": "issue-isolator-id",
        }
        with patch.dict(os.environ, env, clear=True):
            with self.assertRaisesRegex(ValueError, "BAND_ISSUE_ISOLATOR_API_KEY"):
                build_agent_config()

    def test_remote_agent_roles_are_defined(self):
        self.assertEqual(
            set(ROLE_NOTES),
            {"intake", "planner", "engineer", "tester", "reviewer", "issue-isolator"},
        )
        self.assertEqual(set(ROLE_TARGETS), set(ROLE_NOTES))
        self.assertEqual(set(ROLE_TARGET_LABELS), set(ROLE_NOTES))

    def test_remote_agent_cli_uses_defined_roles(self):
        self.assertIsNotNone(remote_agent_main)

    def test_direct_adapter_mentions_next_role(self):
        async def run_case():
            completions = FakeCompletions("what_wrong: scoped issue")
            client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
            adapter = ProofGateDirectAdapter(
                role="planner",
                llm_client=client,
                model="openai/gpt-oss-20b",
            )
            tools = FakeTools()

            await adapter.on_message(
                msg=FakeMessage("Fix login whitespace."),
                tools=tools,
                history=SimpleNamespace(raw=[]),
                participants_msg=None,
                contacts_msg=None,
                is_session_bootstrap=False,
                room_id="room-1",
            )

            self.assertEqual(tools.messages_sent[0]["mentions"], ["@itz1508/engineer"])
            self.assertIn("Fix login whitespace.", completions.calls[0]["messages"][1]["content"])

        import asyncio

        asyncio.run(run_case())

    def test_direct_adapter_handles_empty_provider_response(self):
        async def run_case():
            completions = FakeCompletions("")
            client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
            adapter = ProofGateDirectAdapter(
                role="reviewer",
                llm_client=client,
                model="openai/gpt-oss-20b",
            )
            tools = FakeTools()

            await adapter.on_message(
                msg=FakeMessage("Validate final packet.", sender_name="@itz1508/tester"),
                tools=tools,
                history=SimpleNamespace(raw=[]),
                participants_msg=None,
                contacts_msg=None,
                is_session_bootstrap=False,
                room_id="room-1",
            )

            sent = tools.messages_sent[0]
            self.assertEqual(sent["mentions"], ["@itz1508"])
            self.assertIn("safe_to_apply: false", sent["content"])

        import asyncio

        asyncio.run(run_case())

    def test_direct_adapter_falls_back_when_provider_errors(self):
        async def run_case():
            completions = FakeCompletions(
                "",
                exc=RuntimeError("bad key rc_1234567890abcdef"),
            )
            client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
            adapter = ProofGateDirectAdapter(
                role="engineer",
                llm_client=client,
                model="openai/gpt-oss-20b",
            )
            tools = FakeTools()

            await adapter.on_message(
                msg=FakeMessage("Use fallback."),
                tools=tools,
                history=SimpleNamespace(raw=[]),
                participants_msg=None,
                contacts_msg=None,
                is_session_bootstrap=False,
                room_id="room-1",
            )

            sent = tools.messages_sent[0]
            self.assertEqual(sent["mentions"], ["@itz1508/tester"])
            self.assertIn("handoff_to: Tester", sent["content"])
            self.assertNotIn("provider_status", sent["content"])
            self.assertNotIn("provider_reason", sent["content"])
            self.assertNotIn("rc_1234567890abcdef", sent["content"])

        import asyncio

        asyncio.run(run_case())

    def test_direct_adapter_suppresses_duplicate_incoming_content(self):
        async def run_case():
            adapter = ProofGateDirectAdapter(
                role="reviewer",
                llm_client=None,
                model="openai/gpt-oss-20b",
            )
            tools = FakeTools()
            message = FakeMessage("Same validation summary.", sender_name="@itz1508/tester")

            for _ in range(3):
                await adapter.on_message(
                    msg=message,
                    tools=tools,
                    history=SimpleNamespace(raw=[]),
                    participants_msg=None,
                    contacts_msg=None,
                    is_session_bootstrap=False,
                    room_id="room-1",
                )

            self.assertEqual(len(tools.messages_sent), 1)
            self.assertEqual(tools.messages_sent[0]["mentions"], ["@itz1508"])

        import asyncio

        asyncio.run(run_case())

    def test_direct_adapter_can_run_without_llm_client(self):
        async def run_case():
            adapter = ProofGateDirectAdapter(
                role="tester",
                llm_client=None,
                model="openai/gpt-oss-20b",
            )
            tools = FakeTools()

            await adapter.on_message(
                msg=FakeMessage("Validate fallback."),
                tools=tools,
                history=SimpleNamespace(raw=[]),
                participants_msg=None,
                contacts_msg=None,
                is_session_bootstrap=False,
                room_id="room-1",
            )

            sent = tools.messages_sent[0]
            self.assertEqual(sent["mentions"], ["@itz1508/reviewer"])
            self.assertIn("validation_summary", sent["content"])
            self.assertIn("handoff_to: Reviewer", sent["content"])

        import asyncio

        asyncio.run(run_case())

    def test_issue_isolator_returns_blocked_retry_guidance(self):
        async def run_case():
            adapter = ProofGateDirectAdapter(
                role="issue-isolator",
                llm_client=None,
                model="openai/gpt-oss-20b",
            )
            tools = FakeTools()

            await adapter.on_message(
                msg=FakeMessage("Validation failed.", sender_name="@itz1508/reviewer"),
                tools=tools,
                history=SimpleNamespace(raw=[]),
                participants_msg=None,
                contacts_msg=None,
                is_session_bootstrap=False,
                room_id="room-1",
            )

            sent = tools.messages_sent[0]
            self.assertEqual(sent["mentions"], ["@itz1508/reviewer"])
            self.assertIn("what_failed", sent["content"])
            self.assertIn("safe_to_apply: false", sent["content"])
            self.assertIn("human_action: retry_or_reject", sent["content"])

        import asyncio

        asyncio.run(run_case())

    def test_intake_returns_structured_task_for_planner(self):
        async def run_case():
            adapter = ProofGateDirectAdapter(
                role="intake",
                llm_client=None,
                model="openai/gpt-oss-20b",
            )
            tools = FakeTools()

            await adapter.on_message(
                msg=FakeMessage("Fix login whitespace."),
                tools=tools,
                history=SimpleNamespace(raw=[]),
                participants_msg=None,
                contacts_msg=None,
                is_session_bootstrap=False,
                room_id="room-1",
            )

            sent = tools.messages_sent[0]
            self.assertEqual(sent["mentions"], ["@itz1508/planner"])
            self.assertIn("ready_for_planning: true", sent["content"])
            self.assertIn("handoff_to: Planner", sent["content"])

        import asyncio

        asyncio.run(run_case())


if __name__ == "__main__":
    unittest.main()
