# ProofGate for Band — Submission Content

## Project Title

ProofGate for Band

## Tagline

Five agents, structured context, one controlled retry — real multi-agent resolution through Band.

## Short Description (255 characters max)

Five Band agents collaborate through structured context to resolve software issues. Intake, Plan, Resolution, Issue Isolation, and Finalizing exchange accumulated packets through Band at every handoff. Finalizing delivers the terminal result.

## Long Description

ProofGate for Band is a multi-agent software-resolution workflow where Band is the actual collaboration layer.

Five specialized remote agents exchange structured `proofgate.band.v1` packets through Band at every handoff. Intake captures the human objective into a bounded task. Plan defines measurable requirements and scope. Resolution produces the proposed solution and assesses it criterion-by-criterion. When requirements are not met, Issue Isolation preserves the exact failure, explains why it matters, and supplies a focused recovery instruction. Resolution retries once with that isolation context. Finalizing produces and delivers the terminal result — the workflow ends with no further confirmation required.

The workflow is deterministic: routing decisions are based on `requirements_met`, only one isolation/retry cycle is allowed, and every run reaches one of four terminal outcomes — `completed`, `resolved_after_isolation`, `blocked`, or `failed`.

Band is not a notification layer or output channel. It carries accumulated stage results, evidence, quality assessments, remaining uncertainty, and routing state between agents at every step.

## Problem

Enterprise software-resolution work involves multiple concerns: understanding the request, defining success criteria, producing a solution, assessing quality, handling failure, and synthesizing a result. When a single autonomous agent handles all of this internally, teams cannot inspect what was assessed, what failed, or how recovery happened. The result is an opaque response that must be trusted or rejected wholesale — with no visibility into the reasoning chain between specialized responsibilities.

## Solution

ProofGate decomposes software-resolution work into five specialized Band agents:

| Agent | Responsibility |
|---|---|
| **Intake** | Captures objective, constraints, and bounded task |
| **Plan** | Defines measurable requirements, scope, and risks |
| **Resolution** | Produces the solution and assesses every requirement |
| **Issue Isolation** | Explains failure and supplies focused retry instruction |
| **Finalizing** | Produces and delivers the terminal result — workflow ends |

Each agent produces a bounded stage result with explicit success criteria, evidence, quality assessment, and routing decision. The full workflow context accumulates through Band — not inside a single process.

## Band Usage

Band is the actual collaboration layer:

- Each agent runs as an independent remote agent process connected to a shared Band room.
- Every handoff sends the full accumulated structured packet as a Band message.
- Agents route to the next participant using `@mention` targeting.
- The structured context grows with each agent's contribution — stage results, evidence, uncertainty, and routing decisions accumulate across all handoffs.
- Band carries the collaboration during the workflow at every step, not only at the start or end.

## Workflow

```
Human → Intake → Plan → Resolution
                          ├─ requirements met → Finalizing
                          └─ requirements not met → Issue Isolation
                                                      ↓
                                                Resolution retry
                                                      ↓
                                                  Finalizing
```

Terminal outcomes: `completed` · `resolved_after_isolation` · `blocked` · `failed`

## Failure Handling

Issue Isolation activates only when Resolution reports `requirements_met: false`. It preserves the failed Resolution output, explains:
- What failed and why
- Why it matters for the terminal result
- What information is missing
- How to overcome the failure
- What success looks like after retry

Resolution then retries exactly once with the isolation context. Only one isolation/retry cycle is allowed by design.

## Business Value

- **Traceability**: Every handoff carries accumulated evidence of what was done, assessed, and decided.
- **Specialized responsibility**: Each agent owns one bounded concern rather than handling everything opaquely.
- **Controlled recovery**: Failure handling is part of the workflow contract, not an afterthought.
- **Understandable outcomes**: Terminal results list every participating role's contribution and the routing path taken.
- **Enterprise fit**: Teams can inspect multi-agent work instead of trusting one autonomous response.

## Originality

ProofGate is not a chatbot, a single-agent assistant, or a linear automation chain. It implements:

- **Structured retry with isolation context**: When Resolution fails, the failure is formally isolated and a focused recovery instruction is produced before retry. The retry receives exact failure context rather than a generic "try again."
- **Accumulated evidence through Band**: The collaboration packet grows at every handoff — agents do not start from scratch.
- **Deterministic routing**: Every run reaches a terminal outcome. There is no ambiguous intermediate state.
- **Role separation without orchestrator overhead**: Routing logic is embedded in the packet contract, not in a central controller.

## Technology

- Python 3.11+
- Band SDK (remote agent framework)
- OpenAI-compatible API (Featherless AI provider)
- FastAPI (read-only event mirror)
- SQLite (event recording)
- Static HTML/CSS/JS (presentation website)

## Known Limitations

- Live Band execution requires active Band agent credentials and an OpenAI-compatible service-account key.
- The public website is an explanatory presentation surface — it does not execute or mutate work.
- Edge is not required for the submitted workflow.
- Only one isolation/retry cycle is implemented by design.
- The deterministic local demo proves contract behavior only; it does not prove live Band delivery.

## Future Direction

- Multiple retry cycles with escalating isolation
- Cross-framework agent participation via Band (LangChain, CrewAI agents joining the same room)
- Real-time dashboard showing live packet flow
- Persistent audit trail with searchable workflow history
- Integration with existing CI/CD pipelines
