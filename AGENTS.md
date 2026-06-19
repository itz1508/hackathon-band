# AGENTS.md

## Scope and authority

This file applies to the entire repository. Add a nested `AGENTS.md` only when a subtree needs materially different commands or constraints.

Follow this order:

1. The latest user instruction.
2. This file.
3. Repository code and configuration as implementation evidence.
4. Documentation, reports, transcripts, and generated artifacts as reference material only.

If instructions conflict or the requested scope is unclear, stop and identify the conflict before changing files.

## Project boundary

The active application is the ProofGate Band hackathon demo:

- `proofgate/` contains the Python workflow, FastAPI dashboard backend, Band adapter, remote-agent runner, and local demo.
- `tests/` contains the active unittest suite for the API and workflow.
- `demo/` contains the static dashboard.
- `README.md` and `pyproject.toml` define the primary usage and package boundary.
- `docs/demo_run/` contains checked-in sample artifacts; treat them as examples unless a task explicitly requests regeneration.

Root Qt/C++ files and Alibaba-oriented documents may describe an earlier implementation. Do not treat `ARCHITECTURE.md`, `main.cpp`, `main.qml`, `backend.cpp`, `backend.h`, or `CMakeLists.txt` as active authority without confirming a current runtime or build reference.

## Working rules

- Read broadly enough to establish dependencies and active surfaces; change only files required by the task.
- Inspect `git status --short`, the current branch, and the target files before mutation.
- Preserve unrelated user changes. A dirty worktree requires separating existing changes from the intended patch before editing.
- Prefer the existing Python modules and standard-library unittest workflow over new frameworks or duplicate implementations.
- Do not install packages, change public API behavior, rewrite artifact contracts, or alter agent-role ownership unless the task explicitly requires it.
- Do not commit, push, publish, deploy, or contact live Band agents without explicit user authorization.
- Do not claim that the deterministic local demo proves a live Band integration.

## Secrets and local configuration

- Never read, print, commit, or copy values from `.env`, `agent_config.yaml`, API keys, tokens, or credentials.
- Use `.env.example` and `agent_config.yaml.example` only to understand variable names and structure.
- Do not run `python -m proofgate.config_writer` unless local configuration generation is explicitly requested.
- Do not start `proofgate.remote_agent` processes unless live Band interaction is explicitly in scope.

## Commands

Use the repository's documented commands from the repository root.

Run the test suite:

```powershell
python -m unittest discover -s tests -v
```

Run a local demo without overwriting checked-in samples:

```powershell
python -m proofgate.demo --output "$env:TEMP\proofgate-demo"
```

Run the local dashboard when runtime verification is required:

```powershell
python -m proofgate.server
```

Do not infer that optional dependencies are installed from `pyproject.toml`. If a command fails because a dependency is absent, report the exact failure and ask before installing or changing dependency declarations.

## Validation expectations

- Python workflow, API, or backend changes: run the full unittest command above.
- Static dashboard changes: inspect the diff and verify the served dashboard when browser validation is available.
- Band adapter or remote-agent changes: run local tests first; clearly separate local simulation evidence from any live Band evidence.
- Documentation-only changes: verify links, commands, paths, and consistency with active code; do not claim runtime validation.
- Generated proof packets and transcripts are outputs, not proof by themselves. State the command, exit code, and inspected assertions supporting any validation claim.

## Review guidelines

- Reject changes that expose credentials or weaken `.gitignore` protections for local configuration.
- Preserve the separation between agent recommendations and the human apply/reject decision.
- Check that `safe_to_apply`, validation summaries, and reviewer decisions remain internally consistent.
- Flag claims of live integration, successful validation, or safe mutation when the patch provides only mocked, deterministic, sample, or historical evidence.
- Keep API response contracts synchronized with `tests/test_api.py` and dashboard consumers.

## Completion report

At handoff, report:

- exact files changed;
- commands run and exit codes;
- what passed or failed;
- what remains unverified;
- whether any generated, credential, deployment, or live-service surface was intentionally left untouched.
