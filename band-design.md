# ProofGate for Band — Dashboard Design Specification

## 1. Purpose

Build the hackathon dashboard as a web adaptation of `D:\Dev\Edge\container\Design 1.md`.

The reference document is the visual and interaction knowledge base. This specification translates its operator-shell language into the existing ProofGate HTML/CSS/JavaScript application and the current Edge Job API. It does not import the reference document's PySide6, QML, C++, migration, or full nine-stage workflow architecture.

The dashboard must let an operator:

1. Confirm backend and reviewer readiness.
2. Select one controlled Band case.
3. Start an asynchronous Edge job.
4. Follow responsibility and progress through the real workflow.
5. Review issues, validation evidence, reviewer output, and candidate artifacts.
6. Understand what the evidence proves and does not prove.
7. Choose Apply or Cancel only when the backend returns `awaiting_user_decision`.

The interface is an evidence workstation, not an agent-chat product and not a generic administration dashboard.

---

## 2. Authority and implementation boundary

### Runtime authority

The implementation must inspect and follow these current backend sources:

- `D:\Dev\Edge\edge_backend\api\app.py`
- `D:\Dev\Edge\edge_backend\schemas\job_api.py`
- `D:\Dev\Edge\edge_backend\runtime\job_service.py`
- `D:\Dev\Edge\edge_backend\case_profiles\band_jun19\manifest.json`

The active dashboard files are:

- `demo/index.html`
- `demo/app.js`
- `demo/styles.css`

The dashboard uses the Edge API at `http://127.0.0.1:8790`. It must not create another backend, mock successful results, or silently fall back to checked-in sample data.

### API surface

Use only the current routes:

- `GET /api/health`
- `GET /api/cases?profile_id=band-jun19`
- `POST /api/run`
- `GET /api/jobs/{job_id}`
- `GET /api/results/{job_id}`
- `POST /api/jobs/{job_id}/decision`

Current job statuses:

`queued`, `intake`, `planning`, `apply_resolution`, `issue_isolation`, `external_review`, `sandbox_validation`, `awaiting_user_decision`, `applying`, `finalizing`, `completed`, `cancelled`, `failed`.

Current terminal statuses are `completed`, `cancelled`, and `failed`. `awaiting_user_decision` is not terminal; it is an operator gate.

### Technology fit

- Keep the existing static HTML, CSS, and JavaScript stack.
- Do not add React, Vue, a component framework, charting package, icon package, or build pipeline.
- Use semantic HTML, CSS custom properties, and small JavaScript rendering functions.
- Use the existing Python server only to serve the dashboard.
- Band adapters coordinate participants and handoffs; they do not replace Edge runtime authority.

---

## 3. Reference design translation

### Preserve from `Design 1.md`

- Dark, high-density operator shell.
- Near-black base with cool navy panels.
- Thin hard borders and restrained corner radii.
- Compact uppercase section labels.
- Persistent health and status information.
- A main workspace that stays scannable.
- A right-side evidence drawer for drill-down details.
- Human View, Backend View, and Agent View separation.
- Stage feed with explicit completed, running, blocked, and pending states.
- Evidence rows with commands, exit codes, paths, hashes, and interpretations.
- Status pills and severity colors used semantically.
- Monospace only for technical values.
- Blank and unavailable states instead of invented sample content.
- No claim of success without corresponding backend evidence.

### Adapt rather than discard

Advanced features from the reference are not rejected because they are complex. They are retained when they meet at least one of these conditions:

1. They render fields returned by the current backend.
2. They derive a presentation value transparently from returned fields without changing its meaning.
3. They provide navigation, comparison, filtering, export, or inspection entirely in the client without claiming new backend authority.
4. They are designed as a clearly labeled future-capability surface that stays inactive until its required backend contract exists.

Examples:

- The dependency DAG is valid when actual issue relationships or affected-file edges are returned. Until then, use a truthful single-issue relationship view rather than fake nodes.
- Technical HTML export is valid when it serializes the current result and evidence exactly. It does not require a new backend endpoint.
- A before/after view is valid when the returned candidate patch or post-apply verification provides both states.
- A stage map may be visually advanced, but its active nodes must come from current Job API statuses. Future stages may appear only as explicitly unavailable capability labels, never as completed runtime stages.
- A success-quality panel is valid when it summarizes real checks and attempts. A numeric success-rate score is valid only after a real scoring contract exists or when its derivation is fully declared and approved.
- Restore and rollback views are valid after the backend returns rollback checkpoint and decision data. They may be designed now, but must not expose an active control without an API action.
- Floating detail panels may be implemented as web overlays when they improve comparison or keep the evidence drawer focused.
- Source/target mapping may be used for candidate-versus-controlled-workspace comparison when real path data exists.

Technology-specific mechanisms must still be translated:

- PySide6, QML, QDockWidget, and QSplitter patterns become semantic HTML regions, CSS grid/flex layouts, drawers, sheets, and overlays.
- CMake, Ninja, and native extension requirements are not copied into the web dashboard unless the active repository adopts them independently.
- Desktop-only window behavior becomes responsive web behavior with equivalent information hierarchy.

The only prohibited carryovers are features that fabricate data, create parallel runtime authority, expose unsupported mutations, or misrepresent future capability as current execution.

Use the reference's Register A operator-shell style as the base. Its harder red/green migration register may be used selectively for true source-versus-candidate or unsafe-versus-verified comparisons; it should not color the entire application without semantic reason.

---

## 4. Visual identity

### Color tokens

Use one CSS token source in `:root`:

```css
--bg-shell: #0d0f14;
--bg-panel: #141820;
--bg-panel-raised: #1a2030;
--bg-input: #1e2535;
--border-default: #1e2535;
--border-subtle: #252d3d;
--border-active: #4f6ef7;

--text-primary: #e8eaf0;
--text-secondary: #9aa5c0;
--text-muted: #5a6480;
--text-mono: #c0c8d8;

--accent-blue: #4f6ef7;
--accent-blue-dim: #1e2d5e;
--accent-green: #22c55e;
--accent-green-dim: #0f2a1a;
--accent-amber: #f59e0b;
--accent-amber-dim: #2a1f0d;
--accent-red: #ef4444;
--accent-red-dim: #2a0d0d;
--accent-purple: #a855f7;
--accent-cyan: #22d3ee;
```

### Status mapping

| Meaning | Foreground | Background | Symbol |
|---|---|---|---|
| Healthy / complete | green | green-dim | `✓` |
| Running | blue | dark blue | animated or static `…` |
| Blocked / failed | red | red-dim | `×` |
| Warning / decision required | amber | amber-dim | `!` |
| Pending | muted | panel | `○` |
| Informational | blue | blue-dim | `i` |

Status must always include text. Color alone is insufficient.

### Typography

- UI family: Inter when available, then `Segoe UI`, system sans-serif.
- Technical family: `Cascadia Code`, `JetBrains Mono`, `SFMono-Regular`, monospace.
- Product title: 18–20px, weight 700.
- Screen title: 20–24px, weight 700.
- Panel title: 12–13px, weight 700.
- Uppercase eyebrow: 10px, weight 700, letter spacing `0.08em`.
- Body: 13px.
- Supporting text: 11–12px.
- Technical values: 11–12px monospace.

Avoid oversized marketing typography. Operational content should remain visible above the fold.

### Shape and spacing

- Shell and major panes: square or 2px radius.
- Small cards and controls: maximum 6px radius.
- Pills: allowed only for compact statuses and severities.
- Main spacing unit: 4px.
- Common gaps: 8px, 12px, 16px, 24px.
- Borders: 1px; active selection may use a 2px left edge.
- No drop-shadow stacks, glass blur, glowing cards, or decorative gradients.

---

## 5. Desktop layout

Use a three-layer responsive operator shell adapted from the reference:

```text
┌────────────────────────────────────────────────────────────────────────────┐
│ PROOFGATE / BAND     backend health   reviewer readiness   job id          │
├───────────────┬───────────────────────────────────────┬────────────────────┤
│ CASE TRAY     │ MAIN WORKSPACE                        │ EVIDENCE DRAWER    │
│               │                                       │ [Human][Backend]   │
│ case 01       │ workflow header + active status       │ [Agent]            │
│ case 02       │ stage rail / stage feed               │                    │
│ case 03       │                                       │ selected stage,    │
│ case 04       │ issue/result workspace                │ issue, validation, │
│               │                                       │ reviewer, artifact │
│ exact files   │ proof summary + decision boundary     │                    │
├───────────────┴───────────────────────────────────────┴────────────────────┤
│ status · workflow outcome · progress · event count · controlled target     │
└────────────────────────────────────────────────────────────────────────────┘
```

Recommended desktop proportions:

- Case tray: 240–280px.
- Main workspace: flexible, minimum 520px.
- Evidence drawer: 340–380px when open, 0px when closed.
- Evidence drawer toggle: always visible on the right edge.
- Header: 48–56px.
- Bottom status strip: 28–32px.

The drawer may overlay the main workspace below 1100px. It must not compress the main workspace below usable width.

---

## 5A. Compact implementation profile

Use `C:\Users\itz15\OneDrive\EdgeUpdateFiles\OKComputer_Qt+QML_混合架构\widget_board_qml` as the small implementation analogue.

That reference proves the advanced design can begin with a compact shell rather than implementing every surface at once. Its concrete structure is:

```text
Top toolbar
├── connection state
├── page navigation
└── compact global controls

Left navigation panel
├── selectable source items
└── current selection summary

Central stacked workspace
├── primary page/card
├── live feed panel
└── review panel

Right details panel
├── summary tab
├── record tab
└── snapshot/log tab

Bottom area
├── event log
└── persistent status strip
```

For ProofGate, translate it as follows:

| Small Qt/QML reference | ProofGate web implementation | Real data source |
|---|---|---|
| Top toolbar and connection badge | Compact system header | `/api/health`, current job |
| Folder/navigation dock | Band case tray | `/api/cases?profile_id=band-jun19` |
| Card stack | State-driven main workspace | job status and result |
| `DotPageNav.qml` | Compact workflow-stage navigator | current and visited job stages |
| `LiveFeedPanel.qml` | Client-observed workflow event feed | changes observed while polling `/api/jobs/{job_id}` |
| `SimulationReview.qml` | Validation evidence review | `validation.attempts`, findings, proof refs |
| `SlidePanel.qml` | Collapsible Workflow Evidence Drawer | selected result, issue, reviewer, or artifact |
| Right review/record/snapshot tabs | Human, Backend, and Agent views | current result fields |
| Bottom log dock | Expandable event log | client-observed API transitions and errors |
| Status bar | Persistent system status strip | health, status, outcome, progress, counts |

### Minimum build shape

The first complete dashboard may use this smaller composition:

```text
┌─────────────────────────────────────────────────────────────────────┐
│ ProofGate    ● Edge connected    reviewer ready       [evidence >] │
├──────────────┬───────────────────────────────────────┬──────────────┤
│ BAND CASES   │ ACTIVE WORKSPACE                      │ EVIDENCE     │
│              │                                       │ Human        │
│ ○ Clean      │  Intake → Plan → Resolve → Decision  │ Backend      │
│ ○ Integrity  │                                       │ Agent        │
│ ○ Local path │  current result / issue / proof      │              │
│ ○ Registry   │                                       │              │
├──────────────┴───────────────────────────────────────┴──────────────┤
│ EVENT FEED                                      status · 75% · live │
└─────────────────────────────────────────────────────────────────────┘
```

This is not a reduced-quality version. It is the minimum complete shell from which the advanced DAG, before/after comparison, export, overlays, and richer evidence views can grow without changing the information architecture.

### Compact navigation pattern

Adapt `DotPageNav.qml` into a workflow stage strip:

- Current stage expands into a short labeled segment.
- Adjacent visited stages remain compact dots with tooltips.
- Completed stages are green, active stage blue, operator gate amber, blocked stage red, unvisited stages muted.
- Clicking a visited stage selects its evidence in the drawer; it does not navigate the backend or rerun work.
- Previous/next arrows move through available evidence only.
- Do not show a fixed number of stages when the current run skipped optional stages.

### Compact live feed pattern

Adapt `LiveFeedPanel.qml` as an observed-event ledger, not a simulated log generator.

The frontend may append an event only when it observes:

- Job creation response.
- A changed status, current step, agent, progress, outcome, or error from polling.
- Result availability.
- A decision response.
- A network or API error.

Each row contains:

- Local observation timestamp.
- Severity or event type.
- Human-readable transition.
- Raw source label such as `job status`, `result`, or `decision`.

Permitted controls:

- Auto-scroll toggle.
- Pause/resume visual scrolling; polling must continue unless explicitly designed otherwise.
- Filter by all, status, warning, error, and decision.
- Clear visible client log only; clearing must not alter backend evidence.

Do not copy the reference's seeded messages, random timer, fake latency, service names, or generated success/error events.

### Compact validation review pattern

Adapt `SimulationReview.qml` to returned validation evidence:

- Overall progress is job progress, not a fabricated scenario percentage.
- Passed/failed counts derive from returned validation attempts and findings.
- Pending means the job has not yet returned final validation evidence.
- Each row shows attempt name, exit code, interpretation, command, and artifact reference.
- The progress color follows status semantics; it does not imply safety.
- `Run All` is not available because the current API exposes only `POST /api/run` for the selected case.
- `Details` opens the evidence drawer.
- Client-side Export may serialize the currently returned result exactly.

### Compact slide-panel pattern

Adapt `SlidePanel.qml` into the evidence drawer:

- Expanded width: 340–380px.
- Collapsed state: a narrow 40–48px rail with accessible icons for Human, Backend, Agent, Artifact, and Event views.
- Selecting a rail icon expands the drawer and activates that view.
- The panel may remember its open/closed state locally, but must not persist job evidence outside the backend contract.
- Remove reference-only notifications, analytics, settings, sync, and active-user widgets unless real product features later support them.
- Preserve the smooth 200–250ms width transition with reduced-motion fallback.

### Compact shell acceptance rule

The small shell meets the dashboard requirement when it provides the full operator cycle—case selection, run, progress, evidence, issue handling, proof, and decision boundary—with truthful current data. Advanced visual complexity is optional at first; evidence completeness and authority correctness are not.

---

## 5B. Medium proven dashboard profile

Use `C:\Users\itz15\OneDrive\EdgeUpdateFiles\dashboard_gap_closure_proven.zip` as the medium implementation reference.

The medium reference adds a proven composition layer between the compact shell and the advanced operator dashboard. Its important patterns are architectural, not PySide6-specific:

- A dashboard shell owns global navigation and workspace composition.
- Layout state is separate from rendered widgets.
- Cards are declared by validated schemas.
- Layouts are recursive horizontal/vertical groups containing named slots.
- Slots declare accepted content types and collapse/close behavior.
- A renderer converts normalized layout data into live UI.
- Registries resolve cards, modules, actions, commands, and factories.
- UI reconciles from state instead of treating existing DOM/widgets as authority.
- Empty, incompatible, missing, and invalid states are explicit.
- Attachments pass a normalized intake contract before admission.

For ProofGate, the medium profile is the recommended hackathon build target. It should feel substantially more complete than the compact shell while remaining feasible in the existing static web stack.

### Medium profile layout

```text
DashboardShell
├── SystemHeader
│   ├── product/profile identity
│   ├── backend and reviewer readiness
│   ├── current job identity
│   └── workspace controls
├── WorkspaceLayout
│   ├── CaseSelectionSlot
│   ├── WorkflowExecutionSlot
│   ├── ResultSummarySlot
│   ├── IssueIsolationSlot
│   ├── ValidationEvidenceSlot
│   ├── ProofDecisionSlot
│   └── CandidateArtifactSlot
├── WorkflowEvidenceDrawer
│   ├── HumanViewSlot
│   ├── BackendViewSlot
│   └── AgentViewSlot
└── EventAndStatusRegion
    ├── ObservedEventFeed
    └── SystemStatusStrip
```

The default desktop arrangement is:

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ SYSTEM HEADER                                                            │
├───────────────┬──────────────────────────────────────┬───────────────────┤
│ CASE          │ WORKFLOW + RESULT                    │ EVIDENCE DRAWER   │
│ SELECTION     │                                      │                   │
│               │ ┌─ execution ─────────────────────┐  │ Human             │
│ cases         │ ├─ result summary ────────────────┤  │ Backend           │
│ files         │ ├─ issue / validation ────────────┤  │ Agent             │
│ classification│ └─ proof / decision ──────────────┘  │ Artifact          │
├───────────────┴──────────────────────────────────────┴───────────────────┤
│ OBSERVED EVENT FEED                                  SYSTEM STATUS       │
└──────────────────────────────────────────────────────────────────────────┘
```

### Declarative surface contract

Use a small repo-native JavaScript configuration to describe dashboard surfaces. This is a rendering contract, not a new backend schema:

```js
const DASHBOARD_SURFACES = [
  {
    id: 'case-selection',
    label: 'Band cases',
    region: 'left',
    accepts: ['case-list'],
    collapsible: true,
    visibleWhen: ['ready', 'running', 'result'],
  },
  {
    id: 'workflow-execution',
    label: 'Workflow execution',
    region: 'main',
    accepts: ['job-status', 'stage-feed'],
    collapsible: false,
    visibleWhen: ['running', 'decision', 'result'],
  },
  {
    id: 'validation-evidence',
    label: 'Validation evidence',
    region: 'main',
    accepts: ['validation-attempts', 'proof-refs'],
    collapsible: true,
    visibleWhen: ['decision', 'result'],
  },
  {
    id: 'proof-decision',
    label: 'Proof & decision',
    region: 'main',
    accepts: ['proof-packet', 'decision-controls'],
    collapsible: false,
    visibleWhen: ['decision', 'result'],
  },
];
```

Rules:

- This configuration chooses where known frontend renderers appear.
- It must not define backend stages, fabricate response fields, or execute commands.
- Surface IDs are stable internal frontend keys.
- `visibleWhen` is derived from actual job and result state.
- Unsupported content types render an explicit compatibility error.
- Missing required content renders a truthful empty or unavailable state.

### State-first workspace

Adapt the medium reference's `WorkspaceLayoutState` principle:

```js
const workspaceState = {
  selectedCaseId: null,
  jobId: null,
  job: null,
  result: null,
  activeSurfaceId: 'case-selection',
  drawer: { open: false, view: 'human', selection: null },
  collapsedSurfaces: new Set(),
  observedEvents: [],
};
```

Rendering rules:

1. API responses update state.
2. Render functions reconcile visible surfaces from state.
3. DOM visibility is not used to infer workflow state.
4. Closing or collapsing a surface does not delete evidence from state.
5. Selecting a new drawer item changes only drawer selection.
6. A new job clears prior job/result state through one explicit reset function.
7. Decision controls derive exclusively from `job.status === "awaiting_user_decision"`.

Do not import the medium reference's editable workspace as unrestricted runtime customization. The operator may collapse evidence surfaces or resize columns, but cannot rearrange controls in a way that hides the Apply boundary, current status, errors, or required proof.

### Slot behavior

Each medium-profile surface behaves like a validated slot:

- Header contains title, status, and collapse control when allowed.
- Body has one active renderer.
- Empty state states exactly what is missing.
- Incompatible payload state names the expected and received content shape.
- Critical surfaces cannot close:
  - Workflow execution while active.
  - Proof and decision while awaiting operator decision.
  - Error surface while an unacknowledged failure exists.
- Optional surfaces may collapse:
  - Case selection after a job starts.
  - Validation details.
  - Candidate artifact.
  - Event feed.

### Medium content registry

Use a fixed frontend renderer registry rather than a plugin marketplace:

```js
const RENDERERS = {
  'case-list': renderCaseList,
  'job-status': renderJobStatus,
  'stage-feed': renderStageFeed,
  'result-summary': renderResultSummary,
  'issue-list': renderIssueList,
  'validation-attempts': renderValidationAttempts,
  'proof-refs': renderProofReferences,
  'proof-packet': renderProofPacket,
  'decision-controls': renderDecisionControls,
  'reviewer-evidence': renderReviewerEvidence,
  'candidate-artifact': renderCandidateArtifact,
  'observed-events': renderObservedEvents,
};
```

Registry rules:

- Every key maps to one implementation.
- Unknown keys fail visibly during development.
- Renderers receive state slices and do not fetch independently.
- Only the API client owns network requests.
- Only the decision controller may call the decision endpoint.
- Renderer registration does not grant command or mutation authority.

### Medium profile capabilities

The recommended medium build includes:

1. Compact system header.
2. Four-case selection tray.
3. State-driven run intake.
4. Stage rail plus observed event feed.
5. Result summary metrics derived from returned data.
6. Issue isolation list with drawer drill-down.
7. Validation attempt table with command and exit evidence.
8. Human, Backend, and Agent evidence views.
9. Candidate diff viewer.
10. Explicit Apply/Cancel boundary.
11. Client-side technical JSON/HTML export of the current returned result.
12. Responsive column collapse and persistent drawer toggle.
13. Designed empty, degraded, blocked, failed, and conflict states.

Advanced additions such as dependency DAGs, before/after comparison, multi-panel overlays, saved workspace layouts, and richer exports build on these same slots and state contracts.

### Attachment and external-content gate

Adapt the medium reference's attachment validation when the dashboard later accepts imported evidence or card definitions:

- Raw folders or arbitrary objects are not rendered directly.
- Imported content must declare an ID, display name, version, accepted surface, capabilities, and data shape.
- Validate and normalize before adding it to the renderer registry.
- Reject content requesting unsupported commands or mutation authority.
- Imported content remains reference data unless the backend explicitly recognizes it.

This gate is an advanced-ready design requirement; no file-upload control should appear until import behavior is explicitly requested and implemented.

### Medium profile acceptance rule

The medium profile is complete when:

- All current API states reconcile into the correct surfaces.
- Required surfaces cannot be hidden at authority boundaries.
- Every displayed result maps to returned or transparently derived data.
- Renderer compatibility errors are visible.
- Event feed contains observed transitions only.
- Decision actions have one controlled caller.
- Evidence drawer preserves Human/Backend/Agent separation.
- Layout remains usable at desktop, tablet, and mobile widths.
- Advanced surfaces can be added without replacing API ownership or the workspace state model.

---

## 6. Header and system health

The header is a compact operational strip, not a hero section.

### Left group

- ProofGate wordmark.
- Small `BAND / EDGE` context label.
- Current profile label: `band-jun19` after cases load.

### Right group

- Backend status: `Connected`, `Degraded`, or `Offline`.
- Reviewer status: provider plus `Ready` or `Unavailable`.
- Current job ID, truncated visually with a copy action only if one exists.
- Evidence drawer toggle.

### Truth rules

- `health.status === "ok"` means the configured reviewer is available and authenticated according to the current backend response.
- `degraded` must not be styled as healthy.
- Network failure must show `Offline`; do not retain a stale green state.
- Reviewer availability is readiness only. It is not proof that a review ran.

---

## 7. Case tray

The left tray replaces the reference folder tree. It owns controlled case selection.

### Tray header

- Eyebrow: `CONTROLLED INPUT`.
- Title: `Band cases`.
- Count returned by `/api/cases`.

### Case row

Each row shows:

- Case title.
- One-line description, maximum two lines.
- Issue classification badge:
  - `Clean` when `issue_kind` is null.
  - `Blocking` for `dependency_lock_blocking`.
  - `Isolation required` for `dependency_lock_isolation_required`.
- Exact file names in monospace.

Selected row:

- Blue 2px left border.
- Raised panel background.
- Visible `Selected` label.

Do not invent case counts or case content. If the endpoint returns no cases, show a tray-level empty state and keep Run disabled.

---

## 8. Main workspace states

The main workspace is one surface with state-driven composition. Do not build unrelated pages for every status.

### 8.1 Ready state

Show:

- Eyebrow: `OPERATOR RUN`.
- Selected case title and description.
- Exact file boundary.
- Request message field, 1–1000 characters.
- Reviewer selector only if both values are actually supported by the current backend.
- Primary action: `Run selected case`.
- Boundary note: `Starts evaluation in an isolated job workspace. It does not change the controlled target.`

Do not display all role descriptions as a large permanent card grid. Put concise role responsibility in the stage rail and full explanation in the evidence drawer.

### 8.2 Active state

Show a processing layout derived from the reference execution graph and live feed:

- Current stage header.
- Progress percentage and bar.
- Responsible runtime agent value from `job.agent`, displayed verbatim in Backend View.
- Horizontal stage rail on wide screens.
- Vertical stage feed under 900px.
- Most recent stage emphasized; completed stages remain visible.
- Cancel is not available unless the backend exposes it. Do not invent it.

Polling behavior:

- Poll `GET /api/jobs/{job_id}`.
- Continue through all nonterminal states.
- Stop for `awaiting_user_decision`, `completed`, `cancelled`, or `failed`.
- Fetch results only after the backend indicates they are available.
- If `/api/results` returns `409 result_not_ready`, preserve current state and retry according to the job status; do not show it as fatal immediately.

### 8.3 Awaiting decision state

This is the highest-priority operator state.

Show:

- Amber stage marker.
- `User Apply or Cancel` title.
- Workflow outcome.
- Source integrity statement from `proof_refs.source_unchanged`.
- Validation conclusion.
- Explicit statement: `No automatic apply authority was granted.`
- Apply and Cancel controls.

Apply and Cancel must be visually separated:

- Apply: restrained blue primary action, not green “safe” marketing.
- Cancel: neutral secondary action.
- A short boundary summary sits directly above actions.
- Disable both controls immediately after submission.
- A duplicate decision conflict must be shown as a structured error.

Automated UI tests must not choose Apply.

### 8.4 Completed, cancelled, and failed states

- `completed`: show final outcome and post-apply verification if returned.
- `cancelled`: state that no mutation was performed when evidence confirms it.
- `failed`: show the backend error code and message; never fabricate partial results.
- `blocked`: show issue isolation and required next evidence. Do not show decision buttons.

---

## 9. Stage rail and responsibility model

Use backend status values as stage keys. Human-readable labels explain responsibility without renaming backend data.

| Backend stage | Display title | Responsibility |
|---|---|---|
| `queued` | Queued | Job accepted; work has not started. |
| `intake` | Intake | Validate the selected case and exact file allowlist. |
| `planning` | Planning | Lock scope, validators, and evidence requirements. |
| `apply_resolution` | Apply Resolution | Run the real policy scan and determine whether resolution may proceed. |
| `issue_isolation` | Issue Isolation | Record the exact blocker, failed check, and focused handoff. |
| `external_review` | External Review | Ask the configured reviewer for a bounded resolution when required. |
| `sandbox_validation` | Sandbox Validation | Validate the isolated reviewer candidate. |
| `awaiting_user_decision` | User Apply or Cancel | Wait for explicit operator authority. |
| `applying` | Applying | Copy the approved candidate into the controlled job target. |
| `finalizing` | Finalizing | Run final verification and lock the result. |
| `completed` | Completed | Workflow ended; outcome determines the actual result. |
| `cancelled` | Cancelled | Operator cancelled without apply. |
| `failed` | Failed | Workflow execution failed with a structured error. |

Do not imply that every run visits every stage. Clean cases skip issue isolation, external review, and sandbox validation.

Stage status visuals:

- Completed: green check.
- Current: blue running mark.
- Awaiting operator: amber lock or hand icon.
- Blocked or failed: red cross.
- Not visited: muted hollow circle.

---

## 10. Result workspace

After results are available, the main workspace becomes a dense summary surface with three regions.

### 10.1 Outcome strip

Show:

- Selected case title.
- `workflow_outcome` rendered as readable text but retain raw value in Backend View.
- Issue count.
- Validation attempt count.
- Reviewer state: `not required`, `live`, `unavailable`, or `non-live` based only on returned data.
- Source integrity state.

### 10.2 Workflow result feed

Render `handoff.steps` as compact feed rows:

```text
✓ Intake                  Case and exact files validated.
✓ Planning                Scope and validators locked.
✓ Apply Resolution        Real Edge policy scan executed.
× Issue Isolation         Exact blocker handoff written.
○ User Apply or Cancel    Explicit operator decision required.
```

Each row has:

- Status symbol.
- Backend role label.
- Summary returned by the backend.
- `View evidence` action that opens the right drawer.

Do not add unsupported claims such as duration, token usage, confidence, or success percentage.

### 10.3 Proof decision panel

Always show these returned `proof_packet` fields:

- What is wrong.
- Why it matters.
- How to fix.
- Human action.
- Decision reason.
- `safe_to_apply` as `Automatic apply authorized: Yes/No`.

`safe_to_apply: false` must not be translated to “invalid” unless the backend outcome is blocked. It means automatic apply is not authorized.

---

## 11. Issue isolation

Issue rows remain compact in the main workspace and open full detail in the evidence drawer.

Main row content:

- Severity/status marker.
- `message`.
- `category`.
- `relative_path`.
- One-line reason.

Drawer detail may show returned `details` fields, including:

- Why it matters.
- How to fix.
- Dependency or policy details.
- Exact affected path.
- Validation attempt that produced the finding.

If no issues are returned, show:

`No blocking issue was detected by the configured mechanical check.`

Do not hide the section entirely; a clear zero state is evidence.

---

## 12. Workflow Evidence Drawer

Adapt the reference's persistent right drawer to the web dashboard.

### Drawer behavior

- Fixed to the right edge.
- Width 360px desktop.
- Toggle remains visible while closed.
- Opens from a stage row, issue row, validation attempt, reviewer summary, hash summary, or artifact action.
- One drawer instance; content changes with selection.
- 180–220ms ease-out transition.
- Not a modal on desktop.
- Full-screen sheet on narrow mobile.
- Escape closes it; focus returns to the trigger.

### Drawer tabs

#### Human View

Plain-language summary, maximum five short sentences:

- What happened.
- What result was returned.
- Why it matters.
- What comes next.
- What authority remains with the operator.

Every sentence must be supported by Backend View. Do not show paths, IDs, hashes, or exit codes here.

#### Backend View

Verbatim or minimally formatted key-value evidence:

- Job ID.
- Raw status and workflow outcome.
- Command.
- Exit code.
- Artifact reference.
- Attempt name.
- Source and candidate hashes.
- `source_unchanged`.
- Reviewer `provider`, `live`, `available`, `exit_code`, and `error` when returned.
- Decision record and post-apply verification when returned.

Rules:

- Exit code 0 is green; nonzero is red.
- Empty arrays render as `[]`.
- Null renders as `not returned`, not an empty string.
- Paths and hashes use monospace.
- Long hashes may be visually truncated, but copy must use the complete value.
- Do not rephrase raw evidence values.

#### Agent View

Show external reviewer information only when `result.reviewer` exists:

- Provider.
- Whether execution was live.
- Availability.
- Exit code.
- Error.
- Diagnosis.
- Proposed resolution.
- Affected files.
- Authority implications.
- Expected validation result.

Do not invent an agent transcript. Do not label internal Edge stages as live Band agent messages unless live Band evidence is returned by the backend.

---

## 13. Validation evidence panel

Render every item in `validation.attempts`.

Each attempt row contains:

- Attempt name.
- Command.
- Exit code.
- Interpretation.
- Artifact reference.
- Finding count when derivable from returned findings.

The panel header contains:

- `all_checks_passed`.
- Attempt count.
- Source integrity result.
- Reviewer involvement.

Quality language:

- `Declared checks satisfied` only when `all_checks_passed === true`.
- `Blocked or incomplete` otherwise.
- `Source remained unchanged` only when `source_unchanged === true`.
- `External review not required` only when reviewer data is null and no issue required it.
- `Live reviewer execution recorded` only when `reviewer.live === true`.

Tool execution is supporting evidence. The primary result must explain the outcome and boundary.

---

## 14. Candidate artifact and diff

The candidate artifact is a technical surface.

- Show only when `artifact.content` contains a nonempty value.
- Use a monospace preformatted block.
- Keep horizontal scrolling for long diff lines.
- Include affected-file labels from reviewer output when available.
- Provide Copy, not Apply, inside the artifact panel.
- Do not syntax-color unknown content incorrectly.

When absent, show `No candidate patch was required or returned.`

Artifact existence does not mean validation passed.

---

## 15. Bottom status strip

Adapt the reference status bar into a fixed or sticky compact strip:

- Backend: connected/degraded/offline.
- Raw job status.
- Workflow outcome.
- Progress percentage.
- Selected file count.
- Validation attempt count.
- Decision state.

Use backend values only. Do not show CPU, RAM, token, event, drift, or timing values unless the API later returns them.

---

## 16. Error, empty, and degraded states

Every state must have a designed surface:

| Condition | Required presentation |
|---|---|
| Backend offline | Red health state, startup command, Run disabled |
| Backend degraded | Amber/red reviewer state; cases may remain usable if returned |
| Profile not found | Structured profile error in case tray |
| No cases | Empty tray, no selection, Run disabled |
| Invalid request | Show backend error code and message near request controls |
| Result not ready | Preserve active state and continue based on job status |
| Job not found | Stop polling and show job-not-found error |
| Reviewer unavailable | Show blocked reviewer evidence, not a generic failure |
| No issues | Explicit zero-finding statement |
| No artifact | Explicit no-patch statement |
| Failed job | Error code, message, current step, and last known progress |
| Decision conflict | Explain that the job no longer accepts a decision |

Never replace an error with demo data.

---

## 17. Responsive behavior

### Wide desktop, 1280px and above

- Three-column shell.
- Evidence drawer may remain open.
- Horizontal stage rail.
- Validation attempts use multi-column rows.

### Standard desktop/tablet, 800–1279px

- Case tray 220px.
- Main workspace flexible.
- Drawer overlays content.
- Stage feed may switch to vertical.

### Mobile, below 800px

- Header wraps into two rows.
- Case tray becomes a top collapsible section or horizontal selector.
- Main workspace is one column.
- Evidence drawer becomes a full-screen sheet.
- Decision actions remain visible and stack vertically.
- Technical tables become labeled key-value rows.
- No horizontal page scrolling; only diff blocks may scroll horizontally.

---

## 18. Accessibility

- Use `header`, `nav`, `main`, `aside`, `section`, and `footer` landmarks.
- One `h1`; headings descend without skipped levels.
- Case rows are real buttons or radio-like controls.
- Use `aria-current` or `aria-selected` for selected case and drawer tab.
- Use `aria-live="polite"` for progress; `role="alert"` for failures.
- Focus states use the active blue border and remain visible.
- Drawer traps focus only in mobile modal-sheet mode.
- Drawer close restores focus to its trigger.
- Every icon has a text label or accessible name.
- Status does not rely on color.
- Minimum target size: 40px for primary controls, 32px for compact toolbar controls.
- Respect `prefers-reduced-motion` by removing pulse and slide animation.
- Ensure readable contrast against the dark shell.

---

## 19. Interaction rules

- Do not run a case until selection and request are valid.
- Disable Run while a job is active.
- Prevent multiple poll loops.
- Preserve selected case while rendering results.
- Do not discard visible results when a drawer opens.
- Do not auto-open a popup or export a report.
- Do not automatically choose Apply or Cancel.
- Apply/Cancel appears only for `awaiting_user_decision`.
- Apply is submitted only through `POST /api/jobs/{job_id}/decision` with `{ "decision": "apply" }`.
- Cancel uses `{ "decision": "cancel" }`.
- Disable both controls immediately after one decision request.
- Final UI state must come from the backend response, not optimistic assumptions.

---

## 20. Component map

Build small, repo-native rendering units:

```text
DashboardShell
├── SystemHeader
├── CaseTray
│   ├── CaseTrayHeader
│   └── CaseRow[]
├── MainWorkspace
│   ├── RunIntake
│   ├── ActiveJobHeader
│   ├── StageRail / StageFeed
│   ├── OutcomeStrip
│   ├── WorkflowResultFeed
│   ├── IssueSummary
│   ├── ValidationSummary
│   ├── ProofDecisionPanel
│   ├── CandidateArtifact
│   └── DecisionBoundary
├── WorkflowEvidenceDrawer
│   ├── HumanView
│   ├── BackendView
│   └── AgentView
└── SystemStatusStrip
```

These are conceptual components. Implement them as semantic HTML regions and focused JavaScript render functions; do not introduce a framework.

---

## 21. Build sequence for the implementation agent

1. Load both repositories' `AGENTS.md` files.
2. Capture branch, HEAD, and dirty state.
3. Inspect the current API schemas and JobService result structure.
4. Inventory existing dashboard IDs and event handlers.
5. Establish the CSS token map and shell grid.
6. Build the compact header, case tray, main workspace, evidence drawer, and status strip.
7. Bind existing API calls without changing endpoint contracts.
8. Implement all job states before polishing successful results.
9. Implement Human, Backend, and Agent drawer views from returned fields.
10. Implement decision gating and duplicate-decision handling.
11. Add responsive and reduced-motion behavior.
12. Validate syntax, tests, live HTTP behavior, keyboard use, and visual layout.

Do not rewrite backend ownership or Band role ownership as part of dashboard implementation.

---

## 22. Validation requirements

Run from `D:\Dev\hackaton-band-jun19`:

```powershell
python -m compileall -q proofgate tests
python -m unittest discover -s tests -v
node --check demo/app.js
git diff --check -- demo README.md tests proofgate
```

Runtime verification must use the real local services:

- Edge API on `127.0.0.1:8790`.
- ProofGate dashboard on `127.0.0.1:8787`.

Verify at minimum:

1. Health and reviewer readiness render from `/api/health`.
2. All four current Band cases render from `/api/cases`.
3. A clean case reaches `awaiting_user_decision`.
4. Clean result shows `clean_resolution`, one validation attempt, and unchanged source.
5. `safe_to_apply: false` is shown as no automatic apply authority.
6. Blocking cases show exact issue data and do not expose decision controls.
7. Reviewer-unavailable evidence is distinguished from a successful live review.
8. Result-not-ready does not destroy active job state.
9. Apply is not selected during automated verification.
10. Drawer content maps Human View claims to Backend View evidence.
11. Desktop and mobile layouts are browser-checked when browser tooling is available.

If browser tooling is unavailable, mark visual validation `not_run`. Do not infer visual correctness from HTTP 200 or DOM presence.

---

## 23. Design stop conditions

Stop and report rather than invent when:

- An expected response field is absent from the current backend.
- A requested action has no current endpoint.
- The UI would need a fake result to appear complete.
- Apply would be exposed outside `awaiting_user_decision`.
- The implementation would introduce a second backend.
- Existing dirty changes cannot be separated safely.
- Backend health, cases, or result contracts cannot be verified.
- The design requires changing public API behavior without explicit approval.

---

## 24. Completion report contract

The implementation agent must report:

```text
changed:
commands_run:
result:
evidence:
unverified:
stop_condition:
```

Include exact files changed, command exit codes, test totals, runtime response excerpts, visual validation method, and any intentionally untouched credential, generated, deployment, or live Band surface.

The finished dashboard is acceptable only when it presents current backend truth with the reference design's operator density and evidence hierarchy, without importing unsupported workflow behavior.
