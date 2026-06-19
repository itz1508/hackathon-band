# Remote Agent Definitions

Create these five Band external agents and use the exact config role keys:

- `intake`: captures objective, constraints, missing information, and a bounded task.
- `planner`: defines requirements, scope, risks, and measurable success criteria.
- `resolution`: produces the solution and sets `requirements_met` from criterion-level evidence.
- `issue-isolator`: preserves the failed Resolution, explains why it failed and matters, and supplies one focused recovery instruction.
- `finalizing`: emits the terminal outcome and lists every participating role's successful contribution.

Each agent must return one JSON `stage_results` object matching `proofgate.band.v1`. Do not return loose prose, tool-success-only output, apply decisions, or requests for user choice.
