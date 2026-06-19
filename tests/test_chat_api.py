"""API tests for the ProofGate internal chat server."""
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient


class ChatStatusTests(unittest.TestCase):
    """Test /internal/chat/status endpoint."""

    @patch("proofgate.chat_server._human_client")
    @patch("proofgate.chat_server.settings")
    def test_status_reports_actionable_readiness_without_secrets(self, mock_settings, mock_client_factory):
        from proofgate import chat_server
        from proofgate.chat_server import app
        mock_settings.chat_mode.return_value = "local"
        mock_settings.band_room_id.return_value = "room-1"
        mock_settings.band_intake_handle.return_value = "itz1508/intake"
        mock_settings._env.return_value = "https://app.band.ai/room/1"
        client = mock_client_factory.return_value
        client.health = AsyncMock(return_value={"connected": True, "authenticated": True})
        client.get_room = AsyncMock(return_value={"id": "room-1"})
        client.resolve_participant = AsyncMock(return_value={"id": "intake-1", "handle": "itz1508/intake"})
        supervisor = type("Supervisor", (), {
            "all_running": lambda self: True,
            "status": lambda self: [{"role": str(index), "running": True} for index in range(5)],
        })()
        client = TestClient(app)
        with patch.object(chat_server, "_supervisor", supervisor):
            resp = client.get("/internal/chat/status")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["send_enabled"])
        self.assertEqual(data["agents_running"], 5)
        self.assertNotIn("API_KEY", resp.text)


class ChatSendTests(unittest.TestCase):
    """Test direct Human API submission to Intake."""

    def setUp(self):
        from proofgate import chat_server
        chat_server._submitted_request_ids.clear()

    def _supervisor(self, running=True):
        return type("Supervisor", (), {"all_running": lambda self: running})()

    @patch("proofgate.chat_server._human_client")
    @patch("proofgate.chat_server.settings")
    def test_send_routes_once_to_intake(self, mock_settings, mock_client_factory):
        from proofgate import chat_server
        from proofgate.chat_server import app
        mock_settings.band_room_id.return_value = "room-1"
        mock_settings.band_intake_handle.return_value = "itz1508/intake"
        band = mock_client_factory.return_value
        band.health = AsyncMock(return_value={"connected": True, "authenticated": True})
        band.get_room = AsyncMock(return_value={"id": "room-1"})
        band.resolve_participant = AsyncMock(return_value={"id": "intake-1", "handle": "itz1508/intake"})
        band.send_message = AsyncMock(return_value={"data": {"id": "message-1"}})
        client = TestClient(app)
        with patch.object(chat_server, "_supervisor", self._supervisor()):
            resp = client.post("/internal/chat/send", json={
                "text": "Fix the login timeout.", "client_request_id": "request-1"
            })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["message_id"], "message-1")
        self.assertIsNone(resp.json()["run_id"])
        sent_args = band.send_message.await_args.args
        self.assertEqual(sent_args[0], "room-1")
        self.assertEqual(sent_args[1], "@itz1508/intake Fix the login timeout.")
        self.assertEqual(sent_args[2], [
            {"id": "intake-1", "handle": "itz1508/intake", "name": "Intake Agent"}
        ])

    @patch("proofgate.chat_server._human_client")
    @patch("proofgate.chat_server.settings")
    def test_duplicate_send_is_rejected(self, mock_settings, mock_client_factory):
        from proofgate import chat_server
        from proofgate.chat_server import app
        mock_settings.band_room_id.return_value = "room-1"
        mock_settings.band_intake_handle.return_value = "itz1508/intake"
        band = mock_client_factory.return_value
        band.health = AsyncMock(return_value={"connected": True, "authenticated": True})
        band.get_room = AsyncMock(return_value={})
        band.resolve_participant = AsyncMock(return_value={"id": "intake-1", "handle": "itz1508/intake"})
        band.send_message = AsyncMock(return_value={"id": "message-1"})
        client = TestClient(app)
        body = {"text": "Fix it", "client_request_id": "same-request"}
        with patch.object(chat_server, "_supervisor", self._supervisor()):
            self.assertEqual(client.post("/internal/chat/send", json=body).status_code, 200)
            duplicate = client.post("/internal/chat/send", json=body)
        self.assertEqual(duplicate.status_code, 409)
        self.assertEqual(band.send_message.await_count, 1)

    def test_send_rejects_stopped_agents(self):
        from proofgate import chat_server
        from proofgate.chat_server import app
        client = TestClient(app)
        with patch.object(chat_server, "_supervisor", self._supervisor(False)):
            resp = client.post("/internal/chat/send", json={"text": "Hello"})
        self.assertEqual(resp.status_code, 409)
        self.assertEqual(resp.json()["detail"]["code"], "agents_not_running")

    @patch("proofgate.chat_server._human_client", return_value=None)
    def test_send_rejects_missing_configuration(self, _mock_client_factory):
        from proofgate import chat_server
        from proofgate.chat_server import app
        client = TestClient(app)
        with patch.object(chat_server, "_supervisor", self._supervisor()):
            resp = client.post("/internal/chat/send", json={"text": "Hello"})
        self.assertEqual(resp.status_code, 503)
        self.assertEqual(resp.json()["detail"]["code"], "band_not_configured")

    @patch("proofgate.chat_server._human_client")
    @patch("proofgate.chat_server.settings")
    def test_send_rejects_missing_intake(self, mock_settings, mock_client_factory):
        from proofgate import chat_server
        from proofgate.chat_server import app
        mock_settings.band_room_id.return_value = "room-1"
        mock_settings.band_intake_handle.return_value = "itz1508/intake"
        band = mock_client_factory.return_value
        band.health = AsyncMock(return_value={"connected": True, "authenticated": True})
        band.get_room = AsyncMock(return_value={})
        band.resolve_participant = AsyncMock(return_value=None)
        client = TestClient(app)
        with patch.object(chat_server, "_supervisor", self._supervisor()):
            resp = client.post("/internal/chat/send", json={"text": "Hello"})
        self.assertEqual(resp.status_code, 409)
        self.assertEqual(resp.json()["detail"]["code"], "intake_missing")

    @patch("proofgate.chat_server._human_client")
    @patch("proofgate.chat_server.settings")
    def test_band_rejection_is_secret_safe(self, mock_settings, mock_client_factory):
        from proofgate import chat_server
        from proofgate.band_human_client import BandHumanAPIError
        from proofgate.chat_server import app
        mock_settings.band_room_id.return_value = "room-1"
        mock_settings.band_intake_handle.return_value = "itz1508/intake"
        band = mock_client_factory.return_value
        band.health = AsyncMock(return_value={"connected": True, "authenticated": True})
        band.get_room = AsyncMock(return_value={})
        band.resolve_participant = AsyncMock(return_value={"id": "intake-1", "handle": "itz1508/intake"})
        band.send_message = AsyncMock(side_effect=BandHumanAPIError(403, "secret-provider-detail"))
        client = TestClient(app)
        with patch.object(chat_server, "_supervisor", self._supervisor()):
            resp = client.post("/internal/chat/send", json={"text": "Hello"})
        self.assertEqual(resp.status_code, 503)
        self.assertEqual(resp.json()["detail"]["code"], "band_send_failed")
        self.assertNotIn("secret-provider-detail", resp.text)


class ChatRunTests(unittest.TestCase):
    def test_retry_is_preserved_as_separate_processing_stage(self):
        from proofgate import chat_server
        from proofgate.chat_server import app
        from proofgate.mirror import BandMirror
        from proofgate.remote_agent import fallback_result
        from proofgate.workflow import advance, new_packet

        packet = new_packet(
            run_id="retry-run", task_id="task-1", room_id="room-1",
            objective="Fix it", constraints=["force_failure"],
        )
        for role in ("intake", "planner", "resolution", "issue-isolator", "resolution", "finalizing"):
            packet = advance(packet, fallback_result(role, packet))

        with TemporaryDirectory() as directory:
            mirror = BandMirror(Path(directory) / "mirror.sqlite3")
            mirror.record_event(
                event_key="retry-terminal", packet=packet, event_type="delivery",
                delivery_state="sent", content="terminal",
            )
            client = TestClient(app)
            with patch.object(chat_server, "_mirror", mirror):
                data = client.get("/internal/chat/runs/retry-run").json()
        self.assertIn("resolution", data["stage_results"])
        self.assertIn("resolution-retry", data["stage_results"])
        self.assertEqual(data["workflow_path"].count("resolution"), 1)
        self.assertIn("resolution-retry", data["workflow_path"])


class BandSenderTests(unittest.IsolatedAsyncioTestCase):
    async def test_participant_resolution_normalizes_at_prefix(self):
        from proofgate.band_human_client import BandHumanClient

        client = BandHumanClient(api_key="test")
        client.list_participants = AsyncMock(return_value=[
            {"id": "planner-id", "handle": "itz1508/planner"}
        ])
        participant = await client.resolve_participant("room-1", "@itz1508/planner")
        self.assertEqual(participant["id"], "planner-id")


class AgentSupervisorTests(unittest.TestCase):
    """Test the agent supervisor module."""

    def test_agent_roles_are_five(self):
        from proofgate.agent_supervisor import AGENT_ROLES
        self.assertEqual(len(AGENT_ROLES), 5)
        self.assertIn("intake", AGENT_ROLES)
        self.assertIn("planner", AGENT_ROLES)
        self.assertIn("resolution", AGENT_ROLES)
        self.assertIn("issue-isolator", AGENT_ROLES)
        self.assertIn("finalizing", AGENT_ROLES)

    def test_supervisor_starts_with_no_processes(self):
        from proofgate.agent_supervisor import AgentSupervisor
        sup = AgentSupervisor()
        self.assertFalse(sup.all_running())
        self.assertEqual(len(sup.failed_roles()), 5)

    def test_status_returns_five_entries(self):
        from proofgate.agent_supervisor import AgentSupervisor
        sup = AgentSupervisor()
        status = sup.status()
        self.assertEqual(len(status), 5)
        for s in status:
            self.assertIn("role", s)
            self.assertIn("running", s)


if __name__ == "__main__":
    unittest.main()
