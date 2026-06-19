import unittest

from proofgate.remote_agent import fallback_result
from proofgate.workflow import PacketValidationError, advance, new_packet, stage_result, validate_stage_result


def packet(constraints=None):
    return new_packet(run_id="run-1", task_id="task-1", room_id="room-1",
                      objective="produce a result", constraints=constraints or [])


def run_until_terminal(value):
    while value["to_role"] != "human":
        value = advance(value, fallback_result(value["to_role"], value))
    return value


class WorkflowContractTests(unittest.TestCase):
    def test_roles_exclude_tester_and_user_decision(self):
        value = run_until_terminal(packet())
        stages = [item["stage"] for item in value["stage_results"]]
        self.assertEqual(stages, ["intake", "planner", "resolution", "finalizing"])
        self.assertNotIn("tester", stages)
        self.assertNotIn("reviewer", stages)

    def test_stage_requires_role_success_and_criteria(self):
        result = fallback_result("intake", packet())
        del result["role_success"]
        with self.assertRaises(PacketValidationError):
            validate_stage_result(result)

    def test_successful_resolution_routes_to_finalizing(self):
        value = packet()
        value = advance(value, fallback_result("intake", value))
        value = advance(value, fallback_result("planner", value))
        value = advance(value, fallback_result("resolution", value))
        self.assertEqual(value["to_role"], "finalizing")

    def test_failure_isolated_and_failed_output_preserved(self):
        value = packet(["force_failure"])
        value = advance(value, fallback_result("intake", value))
        value = advance(value, fallback_result("planner", value))
        failed = fallback_result("resolution", value)
        value = advance(value, failed)
        self.assertEqual(value["to_role"], "issue-isolator")
        isolation = fallback_result("issue-isolator", value)
        self.assertEqual(isolation["failed_resolution"], failed)
        for field in ("failure_reason", "why_it_matters", "how_to_overcome", "what_success_looks_like"):
            self.assertTrue(isolation[field])

    def test_retry_receives_isolation_and_only_occurs_once(self):
        value = packet(["force_failure"])
        for role in ("intake", "planner", "resolution", "issue-isolator"):
            value = advance(value, fallback_result(role, value))
        retry = fallback_result("resolution", value)
        self.assertIsNotNone(retry["output"]["retry_context"])
        value = advance(value, retry)
        self.assertEqual(value["retry_count"], 1)
        self.assertEqual(value["to_role"], "finalizing")

    def test_retry_failure_becomes_blocked(self):
        value = packet(["force_failure"])
        for role in ("intake", "planner", "resolution", "issue-isolator"):
            value = advance(value, fallback_result(role, value))
        retry = stage_result("resolution", output={"solution": "still incomplete"},
                             criteria=["complete"], met=[], requirements_met=False,
                             unmet_requirements=["complete"])
        value = advance(value, retry)
        value = advance(value, fallback_result("finalizing", value))
        self.assertEqual(value["final_result"]["outcome"], "blocked")

    def test_second_isolation_is_rejected(self):
        value = packet(["force_failure"])
        for role in ("intake", "planner", "resolution", "issue-isolator"):
            value = advance(value, fallback_result(role, value))
        value["to_role"] = "issue-isolator"
        with self.assertRaises(PacketValidationError):
            advance(value, fallback_result("issue-isolator", value))

    def test_final_lists_every_role_success(self):
        value = run_until_terminal(packet(["force_failure"]))
        expected = {item["stage"] for item in value["stage_results"] if item["stage"] != "finalizing"}
        self.assertEqual(expected, set(value["final_result"]["role_successes"]))
        self.assertEqual(value["final_result"]["outcome"], "resolved_after_isolation")


if __name__ == "__main__":
    unittest.main()
