# ProofGate for Band

Multi-agent change control for AI coding work.

ProofGate turns a risky AI code-change request into a shared Band coordination flow:

```text
Human request
-> @itz1508/planner scopes the change
-> @itz1508/engineer proposes a patch
-> @itz1508/tester simulates validation
-> @itz1508/reviewer accepts or blocks the apply decision
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

See `HACKATHON_REQUIREMENTS.md` for the judging checklist and the remaining live-Band proof step.

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

Run the backend dashboard:

```bash
python -m proofgate.server
```

Open:

```text
http://127.0.0.1:8787
```

Open the dashboard:

```text
demo/index.html
```

`demo/index.html` also works as a static fallback. The backend dashboard is better for the hackathon video because it serves `/api/transcript`, `/api/proof-packet`, and `/api/run-demo`.

No API keys are required for the local demo.

For live Band setup, copy `.env.example` to `.env`, then fill the four Band agent IDs and Band API keys.

An OpenAI-compatible LLM provider key is optional. If the provider is missing or rejects the request, the remote agents keep the Band workflow moving with deterministic ProofGate handoffs. The checked-in example defaults to Featherless when a key is present:

```text
OPENAI_BASE_URL=https://api.featherless.ai/v1
OPENAI_MODEL=openai/gpt-oss-20b
FEATHERLESS_API_KEY=<local only>
```

LangSmith tracing is optional and separate from the LLM provider key:

```text
LANGSMITH_API_KEY=<local only>
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=proofgate-band-hackathon
```

Install live Band dependencies:

```bash
python -m pip install band-sdk openai python-dotenv
```

Generate the Band SDK config:

```bash
python -m proofgate.config_writer
```

Run one remote agent process per terminal:

```bash
python -m proofgate.remote_agent planner
python -m proofgate.remote_agent engineer
python -m proofgate.remote_agent tester
python -m proofgate.remote_agent reviewer
```

Band's remote-agent docs require the live remote process to keep running so the platform can deliver chat-room messages to the agent.

## Repository Layout

```text
proofgate/                 Core demo engine
proofgate/server.py        Local backend dashboard and JSON API
proofgate/band_adapter.py  Band SDK integration boundary
proofgate/remote_agent.py  Band SDK remote-agent runner
proofgate/config_writer.py Local agent_config.yaml generator
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

Use `docs/REMOTE_AGENT_TEMPLATE.md` to create the live Planner, Engineer, Tester, and Reviewer agents in Band.

## Public Demo Boundary

This repository is a hackathon demo. It does not include any private production kernel, private scoring formula, private artifact schema, or protected implementation details.

