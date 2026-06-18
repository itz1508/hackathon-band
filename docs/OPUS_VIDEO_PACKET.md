# Opus Video Packet

Use this packet to create a short hackathon video in Opus.pro or any video editor. The video can work with captions only. Voiceover is optional.

## Video Goal

Show that ProofGate is not just "agents chat together." It is an apply gate for AI code changes.

Core message:

```text
ProofGate turns Band agent collaboration into an auditable human apply gate for AI-generated code changes.
```

## Recommended Length

60 to 90 seconds.

## Assets To Use

| Asset | Purpose |
|---|---|
| Band room screen recording | Proves live Band agent coordination |
| `http://127.0.0.1:8787` dashboard recording | Shows product view, proof packet, diff, validation, and decision |
| Test terminal recording | Shows the repo is working |
| `c:\Users\itz15\OneDrive\Desktop\BAND\full screen.png` | Cover image |

## Demo Command Shots

Show this terminal result briefly:

```powershell
cd D:\Dev\hackaton-band-jun19
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

Expected:

```text
Ran 18 tests
OK
```

## Full Video Structure

### Scene 1: Hook

Visual:

Local dashboard title or Band room participant list.

Caption:

```text
AI coding agents can move fast.
But teams still need proof before apply.
```

Voiceover, optional:

```text
AI coding agents can generate patches quickly, but teams still need proof before a change reaches apply.
```

### Scene 2: Product Name

Visual:

ProofGate dashboard at `http://127.0.0.1:8787`.

Caption:

```text
ProofGate for Band
A multi-agent apply gate for AI code changes.
```

Voiceover, optional:

```text
ProofGate for Band is a multi-agent apply gate for AI code changes.
```

### Scene 3: Live Band Agents

Visual:

Band room with participants panel showing Intake, Planner, Engineer, Tester, Reviewer, and optionally Issue Isolator.

Caption:

```text
Band is the live coordination layer.
Each agent has one job.
```

Voiceover, optional:

```text
Band is the coordination layer. Each remote agent has one narrow responsibility.
```

### Scene 4: Success Path

Visual:

Clean Band handoff chain.

Caption:

```text
Success path:
Human -> Intake -> Planner -> Engineer -> Tester -> Reviewer -> Human
```

Voiceover, optional:

```text
The success path starts with a human request. Intake structures it, Planner scopes it, Engineer proposes a patch, Tester validates it, and Reviewer sends the final proof packet to the human.
```

### Scene 5: What The Agents Produce

Visual:

Band messages or dashboard proof packet.

Caption:

```text
The output is not just code.
It is a proof packet.
```

Voiceover, optional:

```text
The output is not just code. It is a proof packet with scope, diff, validation, and an apply decision.
```

### Scene 6: Dashboard Proof

Visual:

Dashboard showing transcript, proof packet, simulated diff, validation, and Ready for human apply.

Caption:

```text
Proof packet:
what is wrong
why it matters
how to fix it
simulated diff
validation summary
safe_to_apply
```

Voiceover, optional:

```text
The dashboard shows the transcript, the proof packet, the simulated diff, validation results, and the final apply decision.
```

### Scene 7: Failure Path

Visual:

If you do not have a live failure recording, show the agent list or docs, then overlay the caption.

Caption:

```text
Failure path:
Reviewer -> Issue Isolator -> Reviewer -> Human
safe_to_apply: false
```

Voiceover, optional:

```text
When validation fails, ProofGate does not pretend success. Reviewer can send the issue to the Issue Isolator, and the human receives a blocked decision with retry guidance.
```

### Scene 8: Tests

Visual:

Terminal with tests.

Caption:

```text
18 tests passing
Public GitHub repo ready
```

Voiceover, optional:

```text
The demo repo is public, tested, and ready for judging.
```

### Scene 9: Close

Visual:

Dashboard decision card: Ready for human apply.

Caption:

```text
ProofGate makes AI coding safer:
agents collaborate,
proof is recorded,
humans decide apply.
```

Voiceover, optional:

```text
ProofGate makes AI coding safer: agents collaborate, proof is recorded, and humans decide apply.
```

## One-Minute Voiceover

```text
This is ProofGate for Band.

AI coding agents can generate patches quickly, but teams still need proof before a change reaches apply.

ProofGate uses Band as the live coordination layer between specialized agents. Intake turns a raw request into a structured task. Planner scopes the change. Engineer proposes the patch. Tester validates behavior and scope. Reviewer sends the final proof packet to the human.

The demo fixes a login validator so whitespace-only emails are rejected. The output is not just code. It is a proof packet with what is wrong, why it matters, how to fix it, a simulated diff, validation summary, and safe_to_apply.

If validation fails, ProofGate can route the issue to an Issue Isolator and return safe_to_apply false with retry guidance.

ProofGate turns Band agent collaboration into an auditable human apply gate for AI-generated code changes.
```

## No-Voice Caption Script

Use this if the video has no speaking.

```text
ProofGate for Band

AI coding agents can move fast.
Teams still need proof before apply.

Band is the live coordination layer.

Success path:
Human -> Intake -> Planner -> Engineer -> Tester -> Reviewer -> Human

Intake structures the request.
Planner scopes the change.
Engineer proposes the patch.
Tester validates behavior and scope.
Reviewer sends the proof packet.

The output is not just code.
It is a proof packet.

Proof packet includes:
problem
impact
fix
simulated diff
validation
safe_to_apply

Failure path:
Reviewer -> Issue Isolator -> Reviewer -> Human

Unsafe changes return safe_to_apply: false.

The dashboard shows transcript, proof packet, diff, validation, and decision.

18 tests passing.
Public GitHub repo ready.

ProofGate turns Band agent collaboration into an auditable human apply gate.
```

## Submission Description Shortener

Use this in the video description:

```text
ProofGate for Band is a multi-agent apply gate for AI code changes. Band remote agents coordinate request intake, planning, patch proposal, validation, review, and optional issue isolation. The final output is a proof packet that tells the human whether a change is safe to apply.
```
