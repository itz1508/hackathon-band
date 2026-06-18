# Hackathon Requirements Check

Source: Band of Agents Hackathon page, checked 2026-06-18.

## Requirement Mapping

| Requirement | ProofGate status | Repo evidence |
|---|---|---|
| At least 3 agents | Met in demo | `@Planner`, `@Engineer`, `@Tester`, `@Reviewer` in `proofgate/core.py` |
| Agents collaborate through Band | Partially met in repo, requires live room proof for final submission | Local runner uses Band-style room, `@mention` routing, task events, and role handoff; `docs/BAND_INTEGRATION.md` documents live Band mapping |
| Meaningful Band usage | Designed for requirement | Band-style room is the workflow backbone, not a final notification step |
| Enterprise workflow | Met | Multi-agent software change control and human apply decision |
| Public GitHub repository | Must be public before submission | `https://github.com/itz1508/hackathon-band` |
| Demo application platform | Met as static demo | `demo/index.html` |
| Application URL | Needs hosting if lablab form requires URL | Can use GitHub Pages or any static host for `demo/` |
| Video presentation | Needs recording | Recommended 2-3 minute walkthrough showing room transcript, proof packet, and dashboard |
| Slide presentation | Needs export/upload | Use `SUBMISSION.md` as slide script |

## Honest Compliance Status

ProofGate is ready as a runnable demo package and public repo.

For strongest judging, run or record the workflow inside an actual Band chat room before submitting. The current repo includes the integration boundary and the same message model, but a local transcript is not the same as live Band execution.

## Submission Risk

Main risk:

```text
Judges may require proof that the agents collaborated through Band itself, not only a local Band-style simulator.
```

Mitigation:

1. Create four external agents in Band:
   - Planner
   - Engineer
   - Tester
   - Reviewer
2. Use the same handles and handoff order shown in `proofgate/core.py`.
3. Record the Band chat room showing the handoffs.
4. Include the GitHub repo and dashboard link in the lablab submission.

## Fast Video Script

1. Show the problem: AI coding agents need safe change control.
2. Show Band room participants: Planner, Engineer, Tester, Reviewer, Human.
3. Start with the user request.
4. Show each agent handoff.
5. Show the generated proof packet.
6. Show the dashboard.
7. End with the business value: enterprise teams can use AI coding agents without letting unreviewed output reach apply.

