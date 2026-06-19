# Band Integration

ProofGate runs `intake`, `planner`, `resolution`, `issue-isolator`, and `finalizing` as independent Band remote agents. Each received message must be valid `proofgate.band.v1` JSON. The receiving agent appends one complete `stage_results` record, routes deterministically, and sends the entire accumulated packet to the next Band participant.

Normal routing is Intake → Plan → Resolution → Finalizing. When the first Resolution reports `requirements_met: false`, routing becomes Resolution → Issue Isolation → Resolution retry → Finalizing. A second retry is forbidden.

The adapter records received, outgoing, sent, and failed-delivery events in the SQLite mirror. `fallback_generated` evidence means a deterministic provider fallback was used; it is not live model evidence. Mirror records prove what the adapter observed, while local tests prove only contract behavior.
