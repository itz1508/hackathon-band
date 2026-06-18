# Band Integration Notes

ProofGate uses Band's agent-room model as the coordination surface.

The public Band docs describe:

- agents run in their own environment while Band handles shared coordination;
- agents send commands to Band by REST API and receive messages by WebSocket;
- chat rooms use `@mention` routing;
- humans see the whole room while agents receive messages where they are mentioned;
- platform tools can send messages, events, task progress, and participant updates.

ProofGate maps that model directly:

| ProofGate role | Band handle | Purpose |
|---|---|---|
| Planner Agent | `@Planner` | Scope the task and success criteria |
| Engineer Agent | `@Engineer` | Produce the patch candidate |
| Tester Agent | `@Tester` | Run simulated validation |
| Reviewer Agent | `@Reviewer` | Decide whether the packet reaches human apply |
| Human | `@Human` | Final approve or reject action |

## Live Setup Boundary

The local demo does not commit Band credentials.

For a live room:

1. Create four external agents in Band.
2. Store each agent UUID and API key outside git.
3. Export the environment variables listed by `proofgate.band_adapter.describe_live_band_setup()`.
4. Connect each role to the Band SDK.

## Local Demo Reason

The local room runner is included so judges can verify the product workflow without waiting on credentials or external service availability.

