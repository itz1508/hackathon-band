# Hackathon Requirements Check

Source: Band of Agents Hackathon page, checked 2026-06-18.

## Requirement Mapping

| Requirement | ProofGate status | Repo evidence |
|---|---|---|
| At least 3 agents | Met in demo | `@itz1508/planner`, `@itz1508/engineer`, `@itz1508/tester`, `@itz1508/reviewer` in `proofgate/core.py` |
| Agents collaborate through Band | Met in live demo | Four Band remote agents were created and a live Band chat room showed Planner -> Engineer -> Tester -> Reviewer -> Human handoffs |
| Meaningful Band usage | Designed for requirement | Band-style room is the workflow backbone, not a final notification step |
| Enterprise workflow | Met | Multi-agent software change control and human apply decision |
| Public GitHub repository | Met | `https://github.com/itz1508/hackathon-band` |
| Demo application platform | Met as static demo | `demo/index.html` |
| Application URL | Needs hosting if lablab form requires URL | Can use GitHub Pages or any static host for `demo/` |
| Video presentation | Ready to record/upload | Use the clean Band session, local dashboard, and `docs/demo_captions.srt` |
| Slide presentation | Ready from outline | Use `docs/FINAL_SUBMISSION_PACKET.md` slide outline |

## Honest Compliance Status

ProofGate is ready as a runnable demo package, public repo, local dashboard, and live Band room proof.

## Submission Risk

Main risk:

```text
The dashboard is local at http://127.0.0.1:8787, so judges need the video and GitHub repo if no public hosting URL is provided.
```

Mitigation:

1. Record the live Band chat room showing the four-agent handoff.
2. Record the local dashboard at `http://127.0.0.1:8787`.
3. Include the public GitHub repo in the lablab submission.
4. If a public application URL is mandatory, use the GitHub repo URL or deploy the static `demo/` folder.

## Fast Video Script

1. Show the problem: AI coding agents need safe change control.
2. Show Band room participants: Planner, Engineer, Tester, Reviewer, Human.
3. Start with the user request.
4. Show each agent handoff.
5. Show the generated proof packet.
6. Show the dashboard.
7. End with the business value: enterprise teams can use AI coding agents without letting unreviewed output reach apply.

