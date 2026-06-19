# Hackathon Requirement Mapping

The project demonstrates at least three agents collaborating through Band. Its canonical workflow uses five agents across intake, planning, resolution, conditional issue isolation, retry handoff, and finalization.

Band is used during the workflow: every agent receives accumulated structured context through a Band message and sends the updated packet to the next agent. The final message is the terminal result, not the only Band interaction.

Required live acceptance transcript:

```text
Human → Intake → Plan → Resolution(false) → Issue Isolation → Resolution retry → Finalizing
```

Unit tests and deterministic fallback output do not substitute for this live transcript.
