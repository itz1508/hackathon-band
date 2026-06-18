# Remote Agent Template

Use this when creating the live Band demo.

The local ProofGate runner already shows the product flow. The live hackathon proof should show the same flow inside a Band chat room using external agents and Band platform tools.

## Create Remote Agents

Create four required external agents in Band, plus the optional failure-path isolator:

| Agent name | Handle | Responsibility |
|---|---|---|
| ProofGate Planner | `@itz1508/planner` | Scope the user request and define success criteria |
| ProofGate Engineer | `@itz1508/engineer` | Produce the patch candidate and simulated diff |
| ProofGate Tester | `@itz1508/tester` | Validate behavior, scope, and hashes |
| ProofGate Reviewer | `@itz1508/reviewer` | Decide whether the proof packet reaches human apply |
| ProofGate Issue Isolator | `@itz1508/issue-isolator` | Isolate unresolved validation or scope failures before retry |

After creation, copy each agent UUID into local `.env`.

```text
BAND_PLANNER_AGENT_ID=<planner agent UUID>
BAND_ENGINEER_AGENT_ID=<engineer agent UUID>
BAND_TESTER_AGENT_ID=<tester agent UUID>
BAND_REVIEWER_AGENT_ID=<reviewer agent UUID>
BAND_ISSUE_ISOLATOR_AGENT_ID=<issue-isolator agent UUID>
```

The agent API keys also belong in `.env`. Do not commit `.env`.

Band's example remote-agent setup also uses an LLM provider key. For this demo, the runner supports OpenAI-compatible providers, but the key is optional for demo continuity. If the provider is missing or rejects the request, the runner sends deterministic ProofGate handoffs instead of crashing.

Add this locally for Featherless when you want model-generated handoffs:

```text
FEATHERLESS_API_KEY=<your Featherless key>
OPENAI_BASE_URL=https://api.featherless.ai/v1
OPENAI_MODEL=openai/gpt-oss-20b
```

If you use LangSmith tracing, add these separately:

```text
LANGSMITH_API_KEY=<your LangSmith key>
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=proofgate-band-hackathon
```

The LangSmith key is for tracing. It does not replace `FEATHERLESS_API_KEY` or another OpenAI-compatible model provider key.

Generate the ignored Band SDK config:

```bash
python -m proofgate.config_writer
```

This writes `agent_config.yaml`, which follows Band's documented shape:

```yaml
planner:
  agent_id: "<planner-agent-uuid>"
  api_key: "<planner-agent-api-key>"
```

Keep `agent_config.yaml` local only.

## Run Remote Agents

Band remote agents must have a running local process connected through the SDK.

Run one terminal per role:

```bash
python -m proofgate.remote_agent planner
python -m proofgate.remote_agent engineer
python -m proofgate.remote_agent tester
python -m proofgate.remote_agent reviewer
python -m proofgate.remote_agent issue-isolator
```

If dependencies are missing, install the Band SDK stack first:

```bash
python -m pip install band-sdk openai python-dotenv
```

## Required Platform Tools

Use the tools visible in the Band agent environment:

| Tool | How ProofGate uses it |
|---|---|
| `list_available_participants_service` | Find the ProofGate agents before adding them to the room. Check every page until `total_pages` is covered. |
| `add_participant_service` | Add missing Planner, Engineer, Tester, Reviewer, or Issue Isolator agents to the active chat room. |
| `list_chat_participants_service` | Confirm Human, Planner, Engineer, Tester, Reviewer, and optional Issue Isolator are present. |
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
- Planner scopes the request and sends structured scope to @itz1508/engineer.
- Engineer sends a patch candidate and diff to @itz1508/tester.
- Tester sends validation results to @itz1508/reviewer.
- Reviewer sends the final proof packet to the human.
- If validation or scope fails, Reviewer can send the failure to @itz1508/issue-isolator.
- Every handoff must use @mention routing.
- The final proof packet must include what_wrong, why_it_matters, how_to_fix, simulated_diff, validation_summary, safe_to_apply, human_action, and decision_reason.
```

## Role Prompts

### Planner

```text
You are @itz1508/planner for ProofGate.

When the human asks for a code change:
1. restate the task;
2. define scoped_files;
3. define success_criteria;
4. send the result to @itz1508/engineer using a direct message.

Do not produce code. Your job is scope and handoff.
```

### Engineer

```text
You are @itz1508/engineer for ProofGate.

When @itz1508/planner sends scope:
1. produce the smallest patch candidate;
2. produce a unified diff;
3. include before_sha256 and after_sha256 if available;
4. send the patch candidate to @itz1508/tester using a direct message.

Do not approve the change. Your job is candidate implementation.
```

### Tester

```text
You are @itz1508/tester for ProofGate.

When @itz1508/engineer sends a patch candidate:
1. validate the requested behavior;
2. validate the scoped files;
3. report all_tests_passed and scope_ok;
4. send validation_summary to @itz1508/reviewer using a direct message.

Do not approve the human apply decision.
```

### Reviewer

```text
You are @itz1508/reviewer for ProofGate.

When @itz1508/tester sends validation:
1. check scope_ok;
2. check all_tests_passed;
3. assemble the proof packet;
4. send the final result to @itz1508.

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

### Issue Isolator

```text
You are @itz1508/issue-isolator for ProofGate.

When @itz1508/reviewer sends a failed validation or scope concern:
1. identify what_failed;
2. explain why_blocked;
3. identify suspected_cause;
4. write retry_instruction;
5. list evidence_needed;
6. send the blocked-apply explanation to @itz1508/reviewer.

Do not approve the change. Your job is failure isolation and retry guidance.
```

## Expected Live Handoff

```text
@itz1508 -> @itz1508/planner
@itz1508/planner -> @itz1508/engineer
@itz1508/engineer -> @itz1508/tester
@itz1508/tester -> @itz1508/reviewer
@itz1508/reviewer -> @itz1508
```

Failure path:

```text
@itz1508/reviewer -> @itz1508/issue-isolator
@itz1508/issue-isolator -> @itz1508/reviewer
@itz1508/reviewer -> @itz1508 with safe_to_apply: false
```

## Video Proof Checklist

Record these screen moments:

1. Participant list showing the four external agents.
2. Human message to `@itz1508/planner`.
3. Planner direct message to `@itz1508/engineer`.
4. Engineer direct message to `@itz1508/tester`.
5. Tester direct message to `@itz1508/reviewer`.
6. Reviewer proof packet to human.
7. Static dashboard or generated `proof_packet.sample.json`.

