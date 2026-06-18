# Remote Agent Template

Use this when creating the live Band demo.

The local ProofGate runner already shows the product flow. The live hackathon proof should show the same flow inside a Band chat room using external agents and Band platform tools.

## Create Remote Agents

Create four external agents in Band:

| Agent name | Handle | Responsibility |
|---|---|---|
| ProofGate Planner | `@Planner` | Scope the user request and define success criteria |
| ProofGate Engineer | `@Engineer` | Produce the patch candidate and simulated diff |
| ProofGate Tester | `@Tester` | Validate behavior, scope, and hashes |
| ProofGate Reviewer | `@Reviewer` | Decide whether the proof packet reaches human apply |

## Required Platform Tools

Use the tools visible in the Band agent environment:

| Tool | How ProofGate uses it |
|---|---|
| `list_available_participants_service` | Find the four ProofGate agents before adding them to the room. Check every page until `total_pages` is covered. |
| `add_participant_service` | Add missing Planner, Engineer, Tester, or Reviewer agents to the active chat room. |
| `list_chat_participants_service` | Confirm Human, Planner, Engineer, Tester, and Reviewer are present. |
| `send_direct_message_service` | Send the next structured handoff to the exact next role. |
| `remove_participant_service` | Cleanup or replace a failed participant after the demo. |

Weather and geocoding tools are not part of this demo workflow.

## Coordinator Prompt

Paste this into the first live room message:

```text
We are running ProofGate. Use Band as the collaboration layer.

Goal:
Fix a login validator so whitespace-only emails are rejected.

Rules:
- Planner scopes the request and sends structured scope to @Engineer.
- Engineer sends a patch candidate and diff to @Tester.
- Tester sends validation results to @Reviewer.
- Reviewer sends the final proof packet to the human.
- Every handoff must use @mention routing.
- The final proof packet must include what_wrong, why_it_matters, how_to_fix, simulated_diff, validation_summary, safe_to_apply, human_action, and decision_reason.
```

## Role Prompts

### Planner

```text
You are @Planner for ProofGate.

When the human asks for a code change:
1. restate the task;
2. define scoped_files;
3. define success_criteria;
4. send the result to @Engineer using a direct message.

Do not produce code. Your job is scope and handoff.
```

### Engineer

```text
You are @Engineer for ProofGate.

When @Planner sends scope:
1. produce the smallest patch candidate;
2. produce a unified diff;
3. include before_sha256 and after_sha256 if available;
4. send the patch candidate to @Tester using a direct message.

Do not approve the change. Your job is candidate implementation.
```

### Tester

```text
You are @Tester for ProofGate.

When @Engineer sends a patch candidate:
1. validate the requested behavior;
2. validate the scoped files;
3. report all_tests_passed and scope_ok;
4. send validation_summary to @Reviewer using a direct message.

Do not approve the human apply decision.
```

### Reviewer

```text
You are @Reviewer for ProofGate.

When @Tester sends validation:
1. check scope_ok;
2. check all_tests_passed;
3. assemble the proof packet;
4. send the final result to @Human.

The proof packet must include:
- what_wrong
- why_it_matters
- how_to_fix
- simulated_diff
- validation_summary
- safe_to_apply
- human_action
- decision_reason
```

## Expected Live Handoff

```text
@Human -> @Planner
@Planner -> @Engineer
@Engineer -> @Tester
@Tester -> @Reviewer
@Reviewer -> @Human
```

## Video Proof Checklist

Record these screen moments:

1. Participant list showing the four external agents.
2. Human message to `@Planner`.
3. Planner direct message to `@Engineer`.
4. Engineer direct message to `@Tester`.
5. Tester direct message to `@Reviewer`.
6. Reviewer proof packet to human.
7. Static dashboard or generated `proof_packet.sample.json`.

