import tempfile
import threading
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from proofgate.mirror import BandMirror
from proofgate.remote_agent import fallback_result
from proofgate.workflow import advance, new_packet
import proofgate.server as server


class MirrorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.mirror = BandMirror(Path(self.temp.name) / "mirror.sqlite3")

    def tearDown(self):
        self.temp.cleanup()

    def test_concurrent_writes_are_ordered_and_deduplicated(self):
        value = new_packet(run_id="concurrent", task_id="task", room_id="room", objective="test")

        def write(index):
            self.mirror.record_event(event_key=f"event-{index}", packet=value,
                                     event_type="received", delivery_state="delivered", content=str(index))

        threads = [threading.Thread(target=write, args=(index,)) for index in range(20)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.mirror.record_event(event_key="event-1", packet=value,
                                 event_type="received", delivery_state="delivered", content="duplicate")
        events = self.mirror.events("concurrent")
        self.assertEqual(len(events), 20)
        self.assertEqual([item["sequence"] for item in events], list(range(1, 21)))


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.original = server.mirror
        server.mirror = BandMirror(Path(self.temp.name) / "api.sqlite3")
        for item in server.BAND_AGENTS:
            server.mirror.upsert_agent(item.role, item.display_name, item.handle, item.responsibility)
        self.client = TestClient(server.app)

    def tearDown(self):
        server.mirror = self.original
        self.temp.cleanup()

    def test_read_only_api_contract(self):
        value = new_packet(run_id="api-run", task_id="task", room_id="room",
                           objective="mirror", constraints=["force_failure"])
        while value["to_role"] != "human":
            value = advance(value, fallback_result(value["to_role"], value))
        server.mirror.record_event(event_key="one", packet=value, event_type="received",
                                   delivery_state="delivered", content="actual adapter event")
        health = self.client.get("/api/band/health")
        self.assertEqual(health.status_code, 200)
        self.assertFalse(health.json()["live_claim"])
        agents = self.client.get("/api/band/agents").json()["agents"]
        self.assertEqual([item["role"] for item in agents],
                         ["intake", "planner", "resolution", "issue-isolator", "finalizing"])
        self.assertEqual(len(self.client.get("/api/band/runs").json()["runs"]), 1)
        run = self.client.get("/api/band/runs/api-run").json()
        self.assertEqual(run["packet"]["schema_version"], "proofgate.band.v1")
        self.assertEqual(run["packet"]["final_result"]["outcome"], "resolved_after_isolation")
        isolation = next(item for item in run["packet"]["stage_results"] if item["stage"] == "issue-isolator")
        self.assertTrue(isolation["failed_resolution"])
        events = self.client.get("/api/band/runs/api-run/events?after_sequence=0").json()["events"]
        self.assertEqual(events[0]["delivery_state"], "delivered")
        self.assertEqual(self.client.get("/api/band/runs/missing").status_code, 404)


if __name__ == "__main__":
    unittest.main()
