# ProofGate for Band

Multi-agent change control for AI coding work.

ProofGate turns a risky AI code-change request into a shared Band coordination flow:

```text
Human request
-> @Planner scopes the change
-> @Engineer proposes a patch
-> @Tester simulates validation
-> @Reviewer accepts or blocks the apply decision
-> Human sees the proof packet and chooses apply or reject
```

The demo is intentionally small enough to judge quickly, but it shows the core product idea: agents can collaborate through Band, yet a change is not shown as ready to apply until the group has produced a structured proof packet.

## Hackathon Fit

Track: Multi-Agent Software Development

Band usage:

- Agents coordinate by role through a shared room model.
- Messages use Band-style `@mention` routing.
- The transcript records task, tool, result, and decision events.
- Human approval is separate from agent output.
- The demo includes a Band SDK integration stub so the same agents can be connected to real Band external agents.

## Why It Matters

Enterprises want AI coding agents, but they cannot let autonomous agents freely mutate production code. ProofGate gives them a control room where planner, engineer, tester, and reviewer agents coordinate before a change reaches human apply.

## Demo Commands

Run the local proof packet demo:

```bash
python -m proofgate.demo --output docs/demo_run
```

Run tests:

```bash
python -m unittest discover -s tests
```

Open the dashboard:

```text
demo/index.html
```

No API keys are required for the local demo.

## Repository Layout

```text
proofgate/                 Core demo engine
proofgate/band_adapter.py  Band SDK integration boundary
demo/                      Static dashboard for judging/video
docs/                      Submission notes and generated sample packets
tests/                     Unit tests for proof packet behavior
legacy-package-notes.md    Notes about generated source material retained in repo
```

## What The Demo Shows

- A Planner Agent creates scope and success criteria.
- An Engineer Agent proposes a tiny patch.
- A Tester Agent simulates validation and records before/after hashes.
- A Reviewer Agent blocks unsafe output and approves only scoped, validated changes.
- The final packet includes:
  - what is wrong;
  - why it matters;
  - how to fix it;
  - simulated diff;
  - validation summary;
  - human action.

## Real Band Connection

The hackathon demo can run fully offline, but `proofgate/band_adapter.py` mirrors the Band connection boundary from the public docs:

- Band external agents are configured with an agent UUID and API key.
- Agents exchange messages in shared rooms.
- `@mention` routing determines which agent receives work.
- Platform events can capture task progress, tool calls, and decisions.

The adapter is deliberately isolated so credentials never enter the repository.

## Public Demo Boundary

This repository is a hackathon demo. It does not include any private production kernel, private scoring formula, private artifact schema, or protected implementation details.

