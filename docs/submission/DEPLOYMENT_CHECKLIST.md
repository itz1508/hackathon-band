# Deployment Checklist

## Pre-Deployment Verification

- [ ] All asset paths in `demo/index.html` are relative (`./styles.css`, `./app.js`, `./assets/...`)
- [ ] No requests to `localhost`, `127.0.0.1`, or any external API
- [ ] Static local preview works: `python -m http.server 8787 -d demo`
- [ ] Website loads without errors in browser console
- [ ] Video plays if MP4 is present; fallback text shown if absent

## Repository Cleanliness

- [ ] `.gitignore` covers: `.env`, `agent_config.yaml`, `__pycache__/`, `.venv/`
- [ ] No secrets in staged files: `git diff --cached | Select-String -Pattern "API_KEY|api_key|secret|token"`
- [ ] No files over 100 MB (check with `git status` after staging)
- [ ] LICENSE file present (MIT)

## Test Verification

```powershell
python -m unittest discover -s tests -v
python -m compileall -q proofgate
```

- [ ] All tests pass
- [ ] No compilation errors

## Commit Review

- [ ] Review staged changes: `git diff --cached --stat`
- [ ] Commit message is clear and concise
- [ ] No unrelated files included

## GitHub Pages Publishing

1. Push to GitHub: `git push -u origin main`
2. Go to repository Settings → Pages
3. Source: Deploy from a branch
4. Branch: `main`
5. Folder: `/demo` (or configure as root if needed)
6. Wait up to 10 minutes for deployment

**Expected project-site URL:**
```
https://itz1508.github.io/hackathon-band/
```

If using `/demo` subfolder and Pages doesn't support it directly:
- Option A: Move `demo/` contents to root-level `docs/` folder (Pages supports `/docs`)
- Option B: Add a root `index.html` that redirects to `demo/index.html`

## Post-Deployment Verification

- [ ] Application URL loads in browser
- [ ] Stylesheet renders (dark background, colored text)
- [ ] JavaScript runs (artifact tabs switch)
- [ ] Video plays if MP4 was committed
- [ ] All internal links work
- [ ] Footer links resolve (GitHub, Band.ai)

## Cover Image Capture

After deployment:
- [ ] Open the deployed website at full width (1920px)
- [ ] Take a screenshot of the header + workflow panel area
- [ ] Crop to 16:9 aspect ratio
- [ ] Save as PNG or JPG
- [ ] Use as cover image in submission form

## Final Link Verification

- [ ] GitHub repository URL works: `https://github.com/itz1508/hackathon-band`
- [ ] Application URL works: `https://itz1508.github.io/hackathon-band/`
- [ ] Video is accessible (either embedded or linked)
