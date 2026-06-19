# Requirements Document

## Introduction

ProofGate for Band currently exposes internal role identifiers (`intake`, `planner`, `engineer`, `tester`, `reviewer`, `human`, `issue-isolator`) directly in API payloads and in the frontend. The display contract defines exactly four public Band agent identities — Intake Agent, Scanner Agent, Isolator Agent, and Reviewer Agent — with precise step names, status labels, output names, and result field shapes. This feature implements a centralized `ROLE_DISPLAY` registry in the backend and aligns the frontend to consume only the public labels, eliminating any independent label invention in the UI.

The two execution flows are:

- **Success flow** (no issue): Intake → Planning → Phase 01 — Scan → External Review → User Decision. Isolator Agent is shown as muted "Not required".
- **Issue flow**: Intake → Planning → Phase 01 — Scan → Issue Found → Issue Isolation → External Review → User Decision.

---

## Glossary

- **ROLE_DISPLAY**: The centralized Python dict in `proofgate/server.py` that maps every internal role key to its public `agent_name` and `step_name`. No other module may invent or rename these values.
- **Internal role key**: A stable snake_case string used inside the backend to identify a processing step (e.g., `intake`, `planning`, `scan`, `issue_isolation`, `external_review`).
- **Public agent name**: The human-readable label for an agent shown on screen (e.g., `Intake Agent`, `Scanner Agent`).
- **Public step name**: The human-readable label for a step shown on screen (e.g., `Intake`, `Planning`, `Phase 01 — Scan`).
- **Step result object**: A JSON object in the API response representing one completed pipeline step, containing `role`, `agent_name`, `step_name`, `status`, and output-specific fields.
- **Right drawer**: The overlay panel that opens when a user clicks a "Review >" row action on a step card; contains navigation tabs (Summary, Record, Handoff, Dependency Map when available, Run Trace).
- **Success flow**: The execution path taken when no issue is detected during the Scan phase.
- **Issue flow**: The execution path taken when an issue is detected during the Scan phase.
- **Intake Agent**: The public agent owning the `intake` and `planning` internal roles.
- **Scanner Agent**: The public agent owning the `scan` internal role.
- **Isolator Agent**: The public agent owning the `issue_isolation` internal role; only active in the issue flow.
- **Reviewer Agent**: The public agent owning the `external_review` internal role.
- **User Decision**: The final step where the operator applies or cancels the proposed resolution.
- **BandRunner**: The class in `proofgate/server.py` that simulates the Band agent pipeline and produces `job.results`.
- **AgentStepData**: The Pydantic model in `proofgate/server.py` representing a single pipeline step in the API response.

---

## Requirements

### Requirement 1: Centralized ROLE_DISPLAY Registry

**User Story:** As a backend developer, I want a single source of truth that maps internal role keys to public display labels, so that no consumer of the API needs to invent or hardcode agent names or step names independently.

#### Acceptance Criteria

1. THE `proofgate/server.py` Module SHALL define a module-level `ROLE_DISPLAY` dict with exactly five entries: `intake`, `planning`, `scan`, `issue_isolation`, and `external_review`, each mapping to an object with `agent_name` and `step_name` keys.
2. THE `ROLE_DISPLAY` dict SHALL use these exact values:
   - `"intake"` → `{"agent_name": "Intake Agent", "step_name": "Intake"}`
   - `"planning"` → `{"agent_name": "Intake Agent", "step_name": "Planning"}`
   - `"scan"` → `{"agent_name": "Scanner Agent", "step_name": "Phase 01 — Scan"}`
   - `"issue_isolation"` → `{"agent_name": "Isolator Agent", "step_name": "Issue Isolation"}`
   - `"external_review"` → `{"agent_name": "Reviewer Agent", "step_name": "External Review"}`
3. WHEN a step result object is constructed anywhere in `BandRunner`, THE `BandRunner` SHALL derive `agent_name` and `step_name` exclusively from `ROLE_DISPLAY[role]`, never from inline string literals.
4. IF a role key used in `BandRunner` is not present in `ROLE_DISPLAY`, THEN THE `BandRunner` SHALL raise a `KeyError` identifying the missing key rather than silently producing an unlabelled result.

---

### Requirement 2: Step Result Object Shape

**User Story:** As a frontend developer, I want every step result object in the API response to carry both the stable internal role key and the public display labels, so that the UI can render correct labels without any mapping logic of its own.

#### Acceptance Criteria

1. THE `AgentStepData` Model SHALL include the fields `role` (internal key), `agent_name` (public), and `step_name` (public) alongside existing fields.
2. WHEN the API returns a step result for the `intake` role, THE Response SHALL include `"role": "intake"`, `"agent_name": "Intake Agent"`, and `"step_name": "Intake"`.
3. WHEN the API returns a step result for the `planning` role, THE Response SHALL include `"role": "planning"`, `"agent_name": "Intake Agent"`, and `"step_name": "Planning"`.
4. WHEN the API returns a step result for the `scan` role, THE Response SHALL include `"role": "scan"`, `"agent_name": "Scanner Agent"`, and `"step_name": "Phase 01 — Scan"`.
5. WHEN the API returns a step result for the `issue_isolation` role, THE Response SHALL include `"role": "issue_isolation"`, `"agent_name": "Isolator Agent"`, and `"step_name": "Issue Isolation"`.
6. WHEN the API returns a step result for the `external_review` role, THE Response SHALL include `"role": "external_review"`, `"agent_name": "Reviewer Agent"`, and `"step_name": "External Review"`.
7. THE `JobResultsResponse` Model SHALL NOT expose the legacy internal identifiers `planner`, `engineer`, `tester`, `human`, or `issue-isolator` as `role` values in any step result object.

---

### Requirement 3: Intake Agent — Two Visible Substeps

**User Story:** As an operator, I want the Intake Agent to display as two distinct sequential substeps (Intake and Planning) under a single agent identity, so that I can see each responsibility clearly without a separate "Planner Agent" appearing on screen.

#### Acceptance Criteria

1. WHEN a job completes via the success flow, THE API Response SHALL include exactly two step result objects with `"agent_name": "Intake Agent"`: one with `"step_name": "Intake"` and one with `"step_name": "Planning"`.
2. WHEN a job completes via the issue flow, THE API Response SHALL include exactly two step result objects with `"agent_name": "Intake Agent"`: one with `"step_name": "Intake"` and one with `"step_name": "Planning"`.
3. THE `planning` Step Result SHALL include the output-specific fields `input_count` (integer), `selected_files` (list), `scope_summary` (string), and `output_type` with value `"run_plan"`.
4. THE `intake` Step Result SHALL include `output_type` with value `"intake_record"`.
5. THE `AgentStepData` Model SHALL NOT contain a step result with `"agent_name": "Planner Agent"` or `"role": "planner"` in any API response.

---

### Requirement 4: Scanner Agent — Scan Phase Result

**User Story:** As an operator, I want the Scanner Agent step to show a clear scan outcome with the correct output labels and actionable row actions, so that I can tell at a glance whether an issue was found.

#### Acceptance Criteria

1. WHEN a job completes, THE API Response SHALL include exactly one step result with `"role": "scan"`, `"agent_name": "Scanner Agent"`, and `"step_name": "Phase 01 — Scan"`.
2. THE `scan` Step Result SHALL include the output-specific fields `scan_summary` (string), `issue_found` (boolean), `issue_count` (integer), `snapshot_id` (string), and `output_type` with value `"scan_record"`.
3. WHEN `issue_found` is `false`, THE `scan` Step Result SHALL have `issue_count` equal to `0`.
4. WHEN `issue_found` is `true`, THE `scan` Step Result SHALL have `issue_count` greater than or equal to `1`.

---

### Requirement 5: Isolator Agent — Conditional Issue Flow Only

**User Story:** As an operator, I want the Isolator Agent to appear as an active step only when an issue was found during scanning, so that the success flow is not cluttered with inactive isolation steps.

#### Acceptance Criteria

1. WHEN a job completes via the success flow, THE API Response SHALL include one step result with `"role": "issue_isolation"` and `"status": "not_required"` — the step SHALL NOT have `"status": "complete"` or `"status": "active"`.
2. WHEN a job completes via the issue flow, THE API Response SHALL include one step result with `"role": "issue_isolation"` and `"status": "complete"`.
3. THE `issue_isolation` Step Result (when active) SHALL include the output-specific fields `issue_id` (string), `failure_location` (string), `cause_summary` (string), `affected_files` (list), `dependency_graph` (object with `nodes`, `edges`, and `blocked_node` keys), and `output_type` with value `"isolation_result"`.
4. THE `dependency_graph` Object SHALL include at minimum one non-empty `nodes` entry, one non-empty `edges` entry, and a non-empty `blocked_node` string when the issue flow is active.

---

### Requirement 6: Reviewer Agent — External Review Result

**User Story:** As an operator, I want the Reviewer Agent step to show the review provider as metadata only, not as a step name, so that the display contract is clean regardless of which provider (Codex or Claude) performed the review.

#### Acceptance Criteria

1. WHEN a job completes, THE API Response SHALL include exactly one step result with `"role": "external_review"`, `"agent_name": "Reviewer Agent"`, and `"step_name": "External Review"`.
2. THE `external_review` Step Result SHALL include a `provider` field (string) containing the reviewer provider name (e.g., `"Codex"` or `"Claude"`).
3. THE `step_name` Field of the `external_review` step result SHALL always be `"External Review"` regardless of the `provider` value.
4. THE `external_review` Step Result SHALL include the output-specific fields `review_status` (string), `review_summary` (string), `user_action` (string), and `output_type` with value `"review_result"`.
5. THE `external_review` Step Result SHALL include `review_status` with value `"approved_for_user_review"` when the review concludes without a blocking issue.

---

### Requirement 7: Frontend Label Consumption

**User Story:** As a frontend developer, I want `app.js` to read agent names, step names, and status labels exclusively from the API response fields, so that the UI never silently diverges from the backend display contract.

#### Acceptance Criteria

1. THE `app.js` Dashboard SHALL render step cards using only `step.agent_name` and `step.step_name` from the API response, never constructing these labels from `step.role` or any other field.
2. THE `app.js` Dashboard SHALL NOT contain any hardcoded mapping from internal role keys (`intake`, `planning`, `scan`, `issue_isolation`, `external_review`, `planner`, `engineer`, `tester`, `reviewer`, `human`, `issue-isolator`) to display labels.
3. WHEN the API returns a step result with `"agent_name": "Intake Agent"` and `"step_name": "Intake"`, THE Dashboard SHALL display the label `"Intake Agent"` as the agent name and `"Intake"` as the step name.
4. WHEN the API returns a step result with `"step_name": "Phase 01 — Scan"`, THE Dashboard SHALL display exactly `"Phase 01 — Scan"` as the step label — not `"Scan"`, `"scan"`, or any other variant.
5. THE `app.js` Dashboard SHALL display `"Not required"` for any step result with `"status": "not_required"`, without treating it as an error or hiding the step entirely.

---

### Requirement 8: Right Drawer Structure

**User Story:** As an operator, I want each step card to open a right drawer with structured navigation tabs, so that I can review the detailed output for each step without navigating away from the pipeline view.

#### Acceptance Criteria

1. WHEN an operator clicks a "Review >" row action on a step card, THE Dashboard SHALL open a right drawer containing a header with the output title, agent name, step name, and status.
2. THE Right Drawer SHALL NOT use the label "Live View" anywhere in its header or tab navigation.
3. THE Right Drawer SHALL provide navigation tabs labeled exactly: `Summary`, `Record`, `Handoff`, and `Run Trace` for all steps.
4. WHERE the `issue_isolation` step is active, THE Right Drawer SHALL additionally provide a `Dependency Map` navigation tab.
5. THE `Dependency Map` Tab SHALL display at minimum: issue title, issue type, affected files, source node, blocked node, dependency path, failure cause, and suggested review action.

---

### Requirement 9: Public Label Exclusivity

**User Story:** As a product owner, I want all user-visible text in the dashboard to use only the approved public labels, so that the application presents a consistent, professional identity for the Band hackathon demo.

#### Acceptance Criteria

1. THE Dashboard SHALL display exactly these agent name labels and no others: `Intake Agent`, `Scanner Agent`, `Isolator Agent`, `Reviewer Agent`.
2. THE Dashboard SHALL display exactly these step name labels and no others: `Intake`, `Planning`, `Phase 01 — Scan`, `Issue Isolation`, `External Review`, `User Decision`.
3. THE Dashboard SHALL display exactly these output name labels and no others: `Intake Record`, `Run Plan`, `Scan Record`, `Issue Found`, `Snapshot Record`, `Isolation Result`, `Dependency Map`, `Reviewer Handoff`, `Review Result`, `Handoff Result`, `Review Summary`.
4. THE Dashboard SHALL NOT display any snake_case role identifier (e.g., `issue_isolation`, `external_review`, `scan`, `planning`) as a visible label to the operator.
5. THE Dashboard SHALL NOT display the strings `Planner Agent`, `Engineer Agent`, `Tester Agent`, or `Human Agent` as agent labels.

---

### Requirement 10: Test Contract Preservation

**User Story:** As a developer, I want all existing tests in `tests/test_api.py` to continue passing after the display contract changes, so that the API contract used by the dashboard is not broken.

#### Acceptance Criteria

1. WHEN `python -m unittest discover -s tests -v` is executed after all changes, THE Test Suite SHALL exit with code `0` with all tests passing.
2. THE `proofgate.server` Module SHALL continue to export `app`, `_jobs`, `Job`, `JobStage`, and `BandRunner` as importable names at module level.
3. WHEN `BandRunner.run()` is called with `mode="success"`, THE `job.results` dict SHALL continue to include the top-level keys `demo_scenario`, `success_path`, `failure_path`, `transcript`, `proof_packet`, `failure_proof_packet`, `test_cases`, and `artifact`.
4. WHEN `BandRunner.run()` is called with `mode="failure"`, THE `job.results` dict SHALL include `failure_path` with at least one entry whose `role` is `"issue_isolation"`.
5. THE `success_path` list in `job.results` SHALL contain entries for the `intake`, `planning`, `scan`, and `external_review` roles, replacing the legacy `planner`, `engineer`, `tester`, `reviewer`, and `human` entries.
