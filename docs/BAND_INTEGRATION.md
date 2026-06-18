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
| Planner Agent | `@itz1508/planner` | Scope the task and success criteria |
| Engineer Agent | `@itz1508/engineer` | Produce the patch candidate |
| Tester Agent | `@itz1508/tester` | Run simulated validation |
| Reviewer Agent | `@itz1508/reviewer` | Decide whether the packet reaches human apply |
| Human | `@itz1508` | Final approve or reject action |

## Live Setup Boundary

The local demo does not commit Band credentials.

For a live room:

1. Create four external agents in Band.
2. Store each agent UUID and API key outside git.
3. Export the environment variables listed by `proofgate.band_adapter.describe_live_band_setup()`.
4. Connect each role to the Band SDK.

## Platform Tool Usage

The live template uses the Band platform tools visible to remote agents:

- `list_available_participants_service`
- `add_participant_service`
- `list_chat_participants_service`
- `send_direct_message_service`
- `remove_participant_service`

The important tool is `send_direct_message_service`: every ProofGate handoff should move through a direct `@mention` message inside the Band room.

See `docs/REMOTE_AGENT_TEMPLATE.md` for exact role prompts and live-room steps.

## Local Demo Reason

The local room runner is included so judges can verify the product workflow without waiting on credentials or external service availability.

