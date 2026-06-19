"""
ProofGate for Band — Unit Tests
================================
Run: python -m unittest discover -s tests -v
"""

import asyncio
import json
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from proofgate.server import app, _jobs, Job, JobStage, BandRunner


class TestHealth(unittest.TestCase):
    """GET /api/health"""

    def setUp(self):
        self.client = TestClient(app)

    def test_health_returns_ok(self):
        resp = self.client.get("/api/health")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"status": "ok"})


class TestRunJob(unittest.TestCase):
    """POST /api/run"""

    def setUp(self):
        self.client = TestClient(app)
        _jobs.clear()

    def test_run_success_returns_201(self):
        resp = self.client.post(
            "/api/run",
            json={"message": "Fix login validator", "mode": "success"},
        )
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertIn("job_id", data)
        self.assertEqual(data["status"], "queued")
        self.assertIn(data["job_id"], _jobs)

    def test_run_failure_returns_201(self):
        resp = self.client.post(
            "/api/run",
            json={"message": "Fix SQL injection", "mode": "failure"},
        )
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertIn("job_id", data)

    def test_run_invalid_mode_returns_422(self):
        resp = self.client.post(
            "/api/run",
            json={"message": "test", "mode": "invalid"},
        )
        self.assertEqual(resp.status_code, 422)

    def test_run_missing_message_returns_422(self):
        resp = self.client.post(
            "/api/run",
            json={"mode": "success"},
        )
        self.assertEqual(resp.status_code, 422)


class TestJobStatus(unittest.TestCase):
    """GET /api/jobs/{job_id}"""

    def setUp(self):
        self.client = TestClient(app)
        _jobs.clear()

    def test_get_job_queued_status(self):
        job = Job(job_id="test-123", message="test", mode="success")
        _jobs["test-123"] = job
        resp = self.client.get("/api/jobs/test-123")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["job_id"], "test-123")
        self.assertEqual(data["status"], "queued")
        self.assertEqual(data["progress"], 0)

    def test_get_job_running_status(self):
        job = Job(job_id="run-456", message="test", mode="success")
        job.status = JobStage.RUNNING
        job.current_step = "Testing patch"
        job.progress = 65
        job.agent = "@itz1508/tester"
        _jobs["run-456"] = job
        resp = self.client.get("/api/jobs/run-456")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "running")
        self.assertEqual(data["current_step"], "Testing patch")
        self.assertEqual(data["progress"], 65)
        self.assertEqual(data["agent"], "@itz1508/tester")

    def test_get_job_completed_status(self):
        job = Job(job_id="done-789", message="test", mode="success")
        job.status = JobStage.COMPLETED
        job.progress = 100
        _jobs["done-789"] = job
        resp = self.client.get("/api/jobs/done-789")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "completed")
        self.assertEqual(data["progress"], 100)

    def test_get_job_failed_with_error(self):
        job = Job(job_id="fail-001", message="test", mode="success")
        job.status = JobStage.FAILED
        job.error = "Something went wrong"
        _jobs["fail-001"] = job
        resp = self.client.get("/api/jobs/fail-001")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "failed")
        self.assertEqual(data["error"], "Something went wrong")

    def test_get_job_not_found(self):
        resp = self.client.get("/api/jobs/nonexistent")
        self.assertEqual(resp.status_code, 404)


class TestJobResults(unittest.TestCase):
    """GET /api/results/{job_id}"""

    def setUp(self):
        self.client = TestClient(app)
        _jobs.clear()

    def test_get_results_not_found(self):
        resp = self.client.get("/api/results/nonexistent")
        self.assertEqual(resp.status_code, 404)

    def test_get_results_while_running_returns_409(self):
        job = Job(job_id="run-409", message="test", mode="success")
        job.status = JobStage.RUNNING
        _jobs["run-409"] = job
        resp = self.client.get("/api/results/run-409")
        self.assertEqual(resp.status_code, 409)

    def test_get_results_while_queued_returns_409(self):
        job = Job(job_id="queued-409", message="test", mode="success")
        _jobs["queued-409"] = job
        resp = self.client.get("/api/results/queued-409")
        self.assertEqual(resp.status_code, 409)

    def test_get_results_completed_success(self):
        job = Job(job_id="results-ok", message="Fix login validator", mode="success")
        job.status = JobStage.COMPLETED
        job.results = {
            "job_id": "results-ok",
            "status": "completed",
            "scenario": "Fix login validator",
            "demo_scenario": {
                "title": "Login Validator Fix",
                "problem": "No email format or password strength validation",
                "fix": "26 lines added: regex + strength checks",
                "coverage": "10 test cases, 100% coverage",
            },
            "success_path": [
                {
                    "id": "intake",
                    "name": "Intake",
                    "role": "Request Intake",
                    "agent": "@itz1508/intake",
                    "description": "Accepts the request, assesses clarity, and assigns priority.",
                    "details": "## Test",
                    "status": "done",
                }
            ],
            "failure_path": [],
            "transcript": [],
            "proof_packet": {
                "title": "Test Proof",
                "status": "success",
                "scenario": "Fix login validator",
                "what_wrong": "No validation",
                "why_it_matters": "Security issue",
                "how_to_fix": "Add regex",
                "simulated_diff": "--- a/test\n+++ b/test\n@@ -1 +1,2 @@\n-old\n+new",
                "validation_summary": "All good",
                "safe_to_apply": True,
                "human_action": "APPROVED",
                "decision_reason": "Clean patch",
            },
            "failure_proof_packet": {
                "title": "Failure Proof",
                "status": "failure",
                "scenario": "Fix SQL injection",
                "what_wrong": "SQL injection",
                "why_it_matters": "Critical",
                "how_to_fix": "Use parameterized queries",
                "simulated_diff": "--- a/test\n+++ b/test\n@@ -1 +1 @@\n-old\n+new",
                "validation_summary": "Fix verified",
                "safe_to_apply": False,
                "human_action": "APPROVED_WITH_CAVEAT",
                "decision_reason": "Critical vuln fixed",
            },
            "test_cases": [
                {"name": "test_valid_email", "input": "user@example.com", "expected": True, "passed": True},
                {"name": "test_invalid_email", "input": "bad", "expected": False, "passed": True},
            ],
            "artifact": {
                "diff": "--- a/test\n+++ b/test\n@@ -1 +1 @@\n-old\n+new",
                "summary": "Fixed validation",
            },
        }
        _jobs["results-ok"] = job

        resp = self.client.get("/api/results/results-ok")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "completed")
        self.assertEqual(data["scenario"], "Fix login validator")
        self.assertIn("demo_scenario", data)
        self.assertIn("success_path", data)
        self.assertIn("failure_path", data)
        self.assertIn("transcript", data)
        self.assertIn("proof_packet", data)
        self.assertIn("failure_proof_packet", data)
        self.assertIn("test_cases", data)
        self.assertIn("artifact", data)
        self.assertEqual(len(data["test_cases"]), 2)
        self.assertEqual(data["proof_packet"]["safe_to_apply"], True)
        self.assertEqual(data["failure_proof_packet"]["safe_to_apply"], False)

    def test_get_results_no_results_returns_500(self):
        job = Job(job_id="no-results", message="test", mode="success")
        job.status = JobStage.COMPLETED
        job.results = None
        _jobs["no-results"] = job
        resp = self.client.get("/api/results/no-results")
        self.assertEqual(resp.status_code, 500)


class TestBandRunner(unittest.TestCase):
    """Simulated BandRunner unit tests"""

    def setUp(self):
        self.runner = BandRunner(delay_per_step=0.01)

    def test_success_path_completes_job(self):
        job = Job(job_id="test-1", message="Fix login validator", mode="success")
        asyncio.run(self.runner.run(job))
        self.assertEqual(job.status, JobStage.COMPLETED)
        self.assertEqual(job.progress, 100)
        self.assertIsNotNone(job.results)
        self.assertEqual(job.results["scenario"], "Fix login validator")

    def test_failure_path_completes_job(self):
        job = Job(job_id="test-2", message="Fix SQL injection", mode="failure")
        asyncio.run(self.runner.run(job))
        self.assertEqual(job.status, JobStage.COMPLETED)
        self.assertEqual(job.progress, 100)
        self.assertIsNotNone(job.results)
        self.assertEqual(job.results["scenario"], "Fix SQL injection")

    def test_success_path_has_all_fields(self):
        job = Job(job_id="test-3", message="Fix login", mode="success")
        asyncio.run(self.runner.run(job))
        results = job.results
        self.assertIn("demo_scenario", results)
        self.assertIn("success_path", results)
        self.assertIn("failure_path", results)
        self.assertIn("transcript", results)
        self.assertIn("proof_packet", results)
        self.assertIn("failure_proof_packet", results)
        self.assertIn("test_cases", results)
        self.assertIn("artifact", results)
        self.assertEqual(len(results["success_path"]), 6)
        self.assertEqual(len(results["transcript"]), 12)

    def test_failure_path_has_all_fields(self):
        job = Job(job_id="test-4", message="Fix SQL", mode="failure")
        asyncio.run(self.runner.run(job))
        results = job.results
        self.assertIn("demo_scenario", results)
        self.assertIn("success_path", results)
        self.assertIn("failure_path", results)
        self.assertIn("transcript", results)
        self.assertIn("test_cases", results)
        self.assertEqual(len(results["failure_path"]), 4)
        self.assertEqual(len(results["transcript"]), 7)

    def test_runner_handles_error_gracefully(self):
        job = Job(job_id="test-5", message="test", mode="bogus")
        asyncio.run(self.runner.run(job))
        self.assertEqual(job.status, JobStage.FAILED)
        self.assertIsNotNone(job.error)

    def test_success_proof_packet_safe(self):
        job = Job(job_id="test-6", message="Fix login", mode="success")
        asyncio.run(self.runner.run(job))
        self.assertTrue(job.results["proof_packet"]["safe_to_apply"])

    def test_failure_proof_packet_not_safe(self):
        job = Job(job_id="test-7", message="Fix SQL", mode="failure")
        asyncio.run(self.runner.run(job))
        self.assertFalse(job.results["failure_proof_packet"]["safe_to_apply"])

    def test_transcript_timestamps_present(self):
        job = Job(job_id="test-8", message="Fix login", mode="success")
        asyncio.run(self.runner.run(job))
        for msg in job.results["transcript"]:
            self.assertIn("timestamp", msg)
            self.assertIn("agent", msg)
            self.assertIn("message", msg)


class TestFullWorkflow(unittest.TestCase):
    """End-to-end: POST -> poll -> results"""

    def setUp(self):
        self.client = TestClient(app)
        _jobs.clear()

    def test_run_poll_results_success(self):
        # Step 1: Run
        resp = self.client.post(
            "/api/run",
            json={"message": "Fix login validator", "mode": "success"},
        )
        self.assertEqual(resp.status_code, 201)
        job_id = resp.json()["job_id"]

        # Step 2: Poll until completed
        import time
        max_attempts = 30
        status = None
        for _ in range(max_attempts):
            resp = self.client.get(f"/api/jobs/{job_id}")
            self.assertEqual(resp.status_code, 200)
            status = resp.json()["status"]
            if status in ("completed", "failed"):
                break
            time.sleep(0.2)

        self.assertEqual(status, "completed")

        # Step 3: Get results
        resp = self.client.get(f"/api/results/{job_id}")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "completed")
        self.assertIn("proof_packet", data)
        self.assertIn("transcript", data)
        self.assertIn("test_cases", data)
        self.assertEqual(len(data["test_cases"]), 10)

    def test_run_poll_results_failure_mode(self):
        resp = self.client.post(
            "/api/run",
            json={"message": "Fix SQL injection", "mode": "failure"},
        )
        self.assertEqual(resp.status_code, 201)
        job_id = resp.json()["job_id"]

        import time
        for _ in range(30):
            resp = self.client.get(f"/api/jobs/{job_id}")
            status = resp.json()["status"]
            if status in ("completed", "failed"):
                break
            time.sleep(0.2)

        self.assertEqual(status, "completed")

        resp = self.client.get(f"/api/results/{job_id}")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "completed")
        self.assertEqual(len(data["test_cases"]), 3)


if __name__ == "__main__":
    unittest.main()
