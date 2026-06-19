# Recording Checklist

## Before Recording

- [ ] Five Band agents created on band.ai platform
- [ ] Agent IDs and API keys saved in `.env` (not committed)
- [ ] Tester and Reviewer agents not present or unused
- [ ] OpenAI/Featherless service-account key configured in `.env`
- [ ] All secrets hidden from screen (terminal, editor, browser)
- [ ] Successful agent connections confirmed (all 5 processes running)
- [ ] Website open locally (`python -m http.server 8787 -d demo`)
- [ ] Browser notifications disabled
- [ ] Recording resolution: 1920×1080 minimum
- [ ] Recording software tested (OBS, screen capture, etc.)
- [ ] Band room visible in browser with agent names shown

## Success-Path Recording

Capture the full chain:

```
Human → Intake → Plan → Resolution → Finalizing → result delivered
```

Show clearly:
- [ ] Agent names visible in Band room (@itz1508/intake, etc.)
- [ ] Human message sent to Intake
- [ ] Structured packet visible in at least one handoff
- [ ] Role specialization visible (each agent does different work)
- [ ] Terminal outcome displayed (should be `completed`)
- [ ] Workflow ends — no confirmation step after Finalizing

## Isolation-Path Recording (Attempt Only After Success is Secured)

Capture:

```
Human → Intake → Plan → Resolution(fail) → Issue Isolation → Resolution retry → Finalizing → result delivered
```

Show:
- [ ] Resolution reports requirements_not_met
- [ ] Issue Isolation explains the failure
- [ ] Retry receives isolation context
- [ ] Retry succeeds
- [ ] Terminal outcome: `resolved_after_isolation`

## After Recording

- [ ] Trim dead time (pauses, loading, etc.)
- [ ] Verify audio is clear (if narrated)
- [ ] Blur any accidentally-visible secrets
- [ ] Export as MP4 (H.264, AAC audio)
- [ ] Verify file size is under 100 MB (for GitHub)
- [ ] If over 100 MB: compress with ffmpeg or host as GitHub release asset
- [ ] Place at: `demo/assets/proofgate-demo.mp4`
- [ ] Capture a representative frame as poster: `demo/assets/proofgate-video-poster.webp`
- [ ] Verify video plays in browser via the website
