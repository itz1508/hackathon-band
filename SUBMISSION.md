# Hackathon Submission

## Project Name

ProofGate for Band

## One-Line Pitch

A Band-powered multi-agent control room that stops AI coding changes from reaching apply until planner, engineer, tester, and reviewer agents produce a shared proof packet.

## Problem

AI coding agents can generate useful code quickly, but enterprise teams need a clear answer before applying a change:

- What is wrong?
- Why does it matter?
- How will it be fixed?
- Did another agent test it?
- Who approved the final action?

Most agent demos show generation. ProofGate shows controlled coordination before apply.

## Solution

ProofGate coordinates four agents:

| Agent | Responsibility |
|---|---|
| Planner | Convert user request into scoped work and success criteria |
| Engineer | Produce a small patch candidate |
| Tester | Run simulated validation and produce proof fields |
| Reviewer | Decide whether the change can be presented to the human |

The final output is a proof packet and a human action:

```json
{
  "safe_to_apply": true,
  "human_action": "approve_or_reject",
  "decision_reason": "Patch stayed inside scope and validation passed."
}
```

## Band Usage

ProofGate is built around Band's collaboration model:

- shared rooms;
- persistent agent roles;
- `@mention` routing;
- structured task events;
- human-in-the-loop approval.

The included local room runner demonstrates the same message flow without requiring judge credentials. The adapter boundary is in `proofgate/band_adapter.py`.

## Demo Scenario

Task:

```text
Fix a login validator so whitespace-only emails are rejected.
```

Expected flow:

```text
@Planner -> @Engineer -> @Tester -> @Reviewer -> Human
```

Outcome:

- scoped one-file change;
- simulated diff;
- validation summary;
- final reviewer decision;
- proof packet.

## Business Value

ProofGate is useful for teams that want AI coding acceleration without losing change-control discipline:

- software teams adopting AI agents;
- regulated engineering teams;
- internal platform teams;
- security-sensitive automation workflows;
- enterprise code-review pipelines.

## What Is Included

- runnable Python demo;
- static judging dashboard;
- proof packet sample;
- Band integration boundary;
- tests.

## What Is Not Included

This public demo does not include private production workflow internals, private scoring formulas, or proprietary artifact contracts.

