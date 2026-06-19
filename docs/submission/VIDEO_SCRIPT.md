# ProofGate for Band — Video Script

**Target duration:** 3–5 minutes  
**Format:** Screen recording with narration  
**Resolution:** 1920×1080 minimum

---

## 0:00–0:20 — Problem

**On screen:** Title card or website header showing "ProofGate for Band"

**Narration:**
> When AI agents resolve complex software issues, teams get a single autonomous response — but they can't inspect what was assessed, what failed, or how recovery happened. ProofGate changes that.

---

## 0:20–0:45 — ProofGate Overview

**On screen:** Website narrative section and workflow panel visible

**Narration:**
> ProofGate is a multi-agent workflow where five specialized agents collaborate through Band. Each agent produces bounded work with explicit success criteria, and every handoff carries the full accumulated context. Band is the actual collaboration layer — not a wrapper or notification system.

---

## 0:45–1:15 — Five-Agent Workflow

**On screen:** Website workflow panel (left side), scroll through each step

**Narration:**
> The five agents are Intake, Plan, Resolution, Issue Isolation, and Finalizing. Intake captures the objective. Plan defines measurable requirements. Resolution produces the solution and assesses every requirement. If requirements are not met, Issue Isolation explains the failure and supplies a focused retry instruction. Resolution retries once with that context. Finalizing produces and delivers the terminal result — the workflow ends.

**On screen:** Highlight the conditional steps (Issue Isolation, Resolution Retry)

> Issue Isolation and retry are conditional — they activate only when Resolution fails. Only one retry cycle is allowed.

---

## 1:15–2:45 — Real Band Run

**On screen:** Band chat room showing the five agents in a shared room

**Narration:**
> Here is a real Band run. I send a message to the Intake agent in the Band room.

**Show:**
- Human message sent to @itz1508/intake
- Intake processes and sends structured packet to @itz1508/planner
- Planner processes and sends to @itz1508/resolution
- Resolution reports requirements_not_met, sends to @itz1508/issue-isolator
- Issue Isolation explains the failure, sends focused retry to @itz1508/resolution
- Resolution retry succeeds, sends to @itz1508/finalizing
- Finalizing produces and delivers the terminal result — workflow complete

**Narration:**
> Notice that every message is a structured JSON packet — the proofgate.band.v1 schema. Each agent adds its stage result, evidence, and quality assessment. The context accumulates through Band at every handoff.

**On screen:** Expand one packet to show the structure briefly

> The terminal outcome is "resolved_after_isolation" — meaning the first attempt failed, isolation identified the problem, the retry succeeded, and Finalizing delivered the completed result. No further confirmation was needed.

---

## 2:45–3:30 — Submission Website

**On screen:** Navigate through the website

**Narration:**
> The submission website explains the workflow, shows real run artifacts, and presents the recorded Band transcript.

**Show:**
- Header and badges
- Artifact tabs (click through Intake, Plan, Resolution, Isolation, Final Result)
- Terminal panel showing the recorded flow
- Architecture section

> Everything on this page comes from actual workflow output — not invented samples.

---

## 3:30–4:10 — Technical Design and Business Value

**On screen:** Architecture section of the website, then slide 5

**Narration:**
> Each agent runs as an independent Band remote agent process. The Band SDK handles connection and message delivery. An OpenAI-compatible provider generates the agent responses, with deterministic fallback for local testing. A read-only SQLite mirror records all events for audit.

> The business value is simple: teams can inspect how work moved between specialized agents. Every handoff carries evidence. Failure handling is part of the workflow contract. Terminal results list every contributing role.

---

## 4:10–4:30 — Limitations and Closing

**On screen:** Website footer or slide 5 limitations section

**Narration:**
> Live execution requires Band agent credentials and an LLM provider key. The website is an explanatory surface — it does not execute work. Only one retry cycle is implemented by design.

> ProofGate for Band — five agents, structured context, one controlled retry. Thank you.

**On screen:** GitHub URL, Band.ai link

---

## Recording Notes

- Prioritize the real Band run section — judges score "Application of Technology" heavily
- Keep the Band room visible and readable during the live demonstration
- Blur or crop any credential values visible in terminal windows
- Do not show .env or agent_config.yaml contents
- Ensure agent names (@itz1508/intake etc.) are clearly visible in the Band room
- If the isolation path is unstable, record a success path first and add isolation as a bonus
