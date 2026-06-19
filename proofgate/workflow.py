"""Structured ProofGate Band workflow contract and deterministic routing."""
from __future__ import annotations

from copy import deepcopy
from typing import Any

SCHEMA_VERSION = "proofgate.band.v1"
ROLES = ("intake", "planner", "resolution", "issue-isolator", "finalizing")
TERMINAL_OUTCOMES = ("completed", "resolved_after_isolation", "blocked", "failed")
STAGE_FIELDS = (
    "stage", "agent", "responsibility", "inputs_received", "work_completed",
    "role_success", "success_criteria", "success_criteria_met", "output",
    "evidence", "quality_assessment", "remaining_uncertainty",
    "unmet_requirements", "next_action",
)


class PacketValidationError(ValueError):
    """Raised when a Band handoff violates the collaboration contract."""


def new_packet(*, run_id: str, task_id: str, room_id: str, objective: str,
               constraints: list[str] | None = None) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "task_id": task_id,
        "room_id": room_id,
        "objective": objective,
        "current_stage": "intake",
        "from_role": "human",
        "to_role": "intake",
        "retry_count": 0,
        "constraints": constraints or [],
        "stage_results": [],
        "routing": {"reason": "new_request"},
        "final_result": None,
    }


def validate_stage_result(result: dict[str, Any]) -> None:
    missing = [field for field in STAGE_FIELDS if field not in result]
    if missing:
        raise PacketValidationError(f"stage result missing fields: {', '.join(missing)}")
    if result["stage"] not in ROLES:
        raise PacketValidationError(f"unknown stage: {result['stage']}")
    if not isinstance(result["role_success"], str) or not result["role_success"].strip():
        raise PacketValidationError("role_success must describe the role's successful contribution")
    if not isinstance(result["success_criteria"], list) or not result["success_criteria"]:
        raise PacketValidationError("success_criteria must be a non-empty list")
    if not isinstance(result["success_criteria_met"], list):
        raise PacketValidationError("success_criteria_met must be a list")
    if result["stage"] == "resolution" and "requirements_met" not in result:
        raise PacketValidationError("resolution must include requirements_met")
    if result["stage"] == "issue-isolator":
        required = ("failed_stage", "failed_requirement", "failure_point", "failure_reason",
                    "why_it_matters", "missing_information", "how_to_overcome",
                    "what_success_looks_like", "retry_instruction", "failed_resolution")
        absent = [field for field in required if field not in result]
        if absent:
            raise PacketValidationError(f"isolation missing fields: {', '.join(absent)}")


def validate_packet(packet: dict[str, Any]) -> None:
    required = ("schema_version", "run_id", "task_id", "room_id", "objective",
                "current_stage", "from_role", "to_role", "retry_count", "constraints",
                "stage_results", "routing", "final_result")
    missing = [field for field in required if field not in packet]
    if missing:
        raise PacketValidationError(f"packet missing fields: {', '.join(missing)}")
    if packet["schema_version"] != SCHEMA_VERSION:
        raise PacketValidationError("unsupported schema_version")
    if packet["retry_count"] not in (0, 1):
        raise PacketValidationError("only one isolation/retry cycle is allowed")
    if packet["to_role"] not in (*ROLES, "human"):
        raise PacketValidationError(f"unknown recipient: {packet['to_role']}")
    for result in packet["stage_results"]:
        validate_stage_result(result)


def advance(packet: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    """Append one validated role result and route to the next Band agent."""
    validate_packet(packet)
    validate_stage_result(result)
    stage = result["stage"]
    if stage != packet["to_role"]:
        raise PacketValidationError(f"expected {packet['to_role']}, received {stage}")
    updated = deepcopy(packet)
    updated["stage_results"].append(deepcopy(result))
    updated["from_role"] = stage

    if stage == "intake":
        target, reason = "planner", "intake_complete"
    elif stage == "planner":
        target, reason = "resolution", "plan_complete"
    elif stage == "resolution":
        met = bool(result["requirements_met"])
        if updated["retry_count"] == 0 and not met:
            target, reason = "issue-isolator", "requirements_not_met"
        else:
            target, reason = "finalizing", "requirements_met" if met else "retry_exhausted"
    elif stage == "issue-isolator":
        if updated["retry_count"] != 0:
            raise PacketValidationError("a second isolation cycle is not allowed")
        updated["retry_count"] = 1
        target, reason = "resolution", "focused_retry"
    elif stage == "finalizing":
        target, reason = "human", "terminal_result"
        _validate_final_result(result.get("output"), updated)
        updated["final_result"] = deepcopy(result["output"])
    else:  # pragma: no cover
        raise PacketValidationError(f"unknown stage: {stage}")

    updated["current_stage"] = target
    updated["to_role"] = target
    updated["routing"] = {"from": stage, "to": target, "reason": reason}
    validate_packet(updated)
    return updated


def _validate_final_result(final: Any, packet: dict[str, Any]) -> None:
    required = ("outcome", "objective", "role_successes", "final_summary", "resolution",
                "evidence", "isolation_summary", "requirements_met", "unresolved_items",
                "remaining_uncertainty", "recommended_next_step")
    if not isinstance(final, dict):
        raise PacketValidationError("finalizing output must be a final result object")
    missing = [field for field in required if field not in final]
    if missing:
        raise PacketValidationError(f"final result missing fields: {', '.join(missing)}")
    if final["outcome"] not in TERMINAL_OUTCOMES:
        raise PacketValidationError("invalid terminal outcome")
    expected = {item["stage"] for item in packet["stage_results"] if item["stage"] != "finalizing"}
    if not expected.issubset(set(final["role_successes"])):
        raise PacketValidationError("final result must list every participating role's success")


def stage_result(stage: str, *, output: Any, criteria: list[str], met: list[str],
                 requirements_met: bool | None = None, **extra: Any) -> dict[str, Any]:
    """Convenience builder used by deterministic fallback and local tests."""
    result = {
        "stage": stage,
        "agent": stage,
        "responsibility": extra.pop("responsibility", f"Complete the {stage} role contract."),
        "inputs_received": extra.pop("inputs_received", []),
        "work_completed": extra.pop("work_completed", f"{stage} work completed."),
        "role_success": extra.pop("role_success", f"{stage} produced its required structured contribution."),
        "success_criteria": criteria,
        "success_criteria_met": met,
        "output": output,
        "evidence": extra.pop("evidence", []),
        "quality_assessment": extra.pop("quality_assessment", "structured and bounded"),
        "remaining_uncertainty": extra.pop("remaining_uncertainty", []),
        "unmet_requirements": extra.pop("unmet_requirements", []),
        "next_action": extra.pop("next_action", "route according to workflow"),
    }
    if requirements_met is not None:
        result["requirements_met"] = requirements_met
    result.update(extra)
    return result
