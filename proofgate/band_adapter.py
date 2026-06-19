"""Canonical Band agent identities and handoff contract."""
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class BandAgentConfig:
    role: str
    display_name: str
    stage: str
    responsibility: str
    handle: str
    agent_id_env: str
    api_key_env: str


BAND_AGENTS = (
    BandAgentConfig("intake", "Request Intake", "Intake", "Turn the human request into a complete bounded task.", "@itz1508/intake", "BAND_INTAKE_AGENT_ID", "BAND_INTAKE_API_KEY"),
    BandAgentConfig("planner", "Plan Author", "Plan", "Define scope, constraints, measurable criteria, and risks.", "@itz1508/planner", "BAND_PLANNER_AGENT_ID", "BAND_PLANNER_API_KEY"),
    BandAgentConfig("resolution", "Resolution Author", "Resolution", "Produce and assess the requested solution against every requirement.", "@itz1508/resolution", "BAND_RESOLUTION_AGENT_ID", "BAND_RESOLUTION_API_KEY"),
    BandAgentConfig("issue-isolator", "Issue Isolation", "Issue Isolation", "Explain a failed resolution and create a focused recovery instruction.", "@itz1508/issue-isolator", "BAND_ISSUE_ISOLATOR_AGENT_ID", "BAND_ISSUE_ISOLATOR_API_KEY"),
    BandAgentConfig("finalizing", "Result Finalizer", "Finalizing", "Synthesize the terminal result and every role's successful contribution.", "@itz1508/finalizing", "BAND_FINALIZING_AGENT_ID", "BAND_FINALIZING_API_KEY"),
)
ROLE_BY_KEY = {item.role: item for item in BAND_AGENTS}


def describe_live_band_setup() -> list[dict[str, str]]:
    return [asdict(item) for item in BAND_AGENTS]


def describe_live_handoffs() -> list[dict[str, str]]:
    return [
        {"from": "human", "to": "intake"},
        {"from": "intake", "to": "planner"},
        {"from": "planner", "to": "resolution"},
        {"from": "resolution", "to": "finalizing", "when": "requirements_met"},
        {"from": "resolution", "to": "issue-isolator", "when": "requirements_not_met"},
        {"from": "issue-isolator", "to": "resolution", "when": "retry_count=1"},
        {"from": "resolution", "to": "finalizing", "when": "retry_complete"},
    ]
