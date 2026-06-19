# ProofGate for Band

> Five specialized Band agents collaborate through structured context to resolve software issues — with one controlled retry when requirements are not met.

**Built for the [Band of Agents Hackathon](https://lablab.ai/ai-hackathons/band-of-agents-hackathon)**

ProofGate demonstrates real structured collaboration between five Band agents:

```text
Human → Intake → Plan → Resolution
                            ├─ requirements met → Finalizing
                            └─ requirements unmet → Issue Isolation
                                                       ↓
                                                 Resolution retry
                                                       ↓
                                                  Finalizing
```

Band is the collaboration layer. Every handoff carries a `proofgate.band.v1` packet with accumulated stage results, evidence, quality assessment, uncertainty, routing state, and each role's successful contribution. Tool delivery alone never counts as successful role work.

There is no Tester role, separate Reviewer role, Human Apply gate, or user-decision step. Resolution assesses its own output against the Plan. A failed first attempt receives one focused retry through Issue Isolation. Finalizing always produces one of:

- `completed`
- `resolved_after_isolation`
- `blocked`
- `failed`

Finalizing is the terminal delivery stage. It produces the completed result and delivers it. No human confirmation is required after delivery.

## Setup

Copy `.env.example` to `.env`, fill local values, and generate the ignored Band SDK config:

```powershell
python -m proofgate.config_writer
```

Existing Engineer credentials are accepted as aliases for Resolution. Existing Reviewer credentials are accepted as aliases for Finalizing.

Start the five live Band processes in separate terminals:

```powershell
python -m proofgate.remote_agent intake
python -m proofgate.remote_agent planner
python -m proofgate.remote_agent resolution
python -m proofgate.remote_agent issue-isolator
python -m proofgate.remote_agent finalizing
```

Start the read-only conversation mirror API:

```powershell
python -m proofgate.server
```

The API exposes:

```text
GET /api/band/health
GET /api/band/agents
GET /api/band/runs?limit=20
GET /api/band/runs/{run_id}
GET /api/band/runs/{run_id}/events?after_sequence=0
```

Runtime events are stored at `%LOCALAPPDATA%\ProofGate\band_mirror.sqlite3`, or at `PROOFGATE_MIRROR_DB` when set. The API is read-only and does not initiate runs or make decisions.

## Verification

```powershell
python -m unittest discover -s tests -v
```

Local tests and deterministic fallback output prove contract behavior only. They do not prove a live Band delivery. Live evidence must come from adapter-recorded events in the mirror.
