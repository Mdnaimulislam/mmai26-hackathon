# Robotics Strand — SONAIR: Can Your Robotics Evidence Be Trusted Beyond the Lab?

**MultimodalAI'26 Hackathon · 10 June 2026**

---

## Read this first

Read **[STRAND_GUIDE.md](STRAND_GUIDE.md)** for the full challenge brief, track roles, deliverables, and what your team must produce.

---

## What is provided

| Path | Contents |
|---|---|
| `reference/federation.json` | Federation manifest template — fill in your institution details |
| `reference/theme.config.json` | Theme configuration template — fill in your brand colour and logo |
| `reference/iframe-test.html` | Iframe compatibility test — update `src` to your deployed URL |
| `sub-portals/` | Directory for your campus sub-portal files |
| `data/` | Dataset released at hackathon start — see `data/README.md` |
| `validate_submission.py` | Pre-submission validator — run before your demo |
| `.pre-commit-config.yaml` | Pre-commit hooks — install once, runs the validator automatically |

---

## Create your team branch immediately after cloning

```bash
git checkout -b your-team-name
```

All your work goes on your team branch. **Do not commit directly to the robotic branch.**
Your `node.id` in `reference/federation.json` must match your branch name exactly.

---

## Quick start

```bash
# 1. Fork and clone this repository
# 2. Create your team branch
git checkout -b your-team-name

# 3. Install pre-commit hooks (runs the validator automatically on each commit)
pip install pre-commit
pre-commit install

# 4. Deploy your sub-portal (GitHub Pages recommended)
#    Enable: Settings → Pages → Source: main branch → /sub-portals/your-team-name
#    Confirm the live URL loads in an incognito browser before filling in node.url

# 5. Fill in reference/federation.json and reference/theme.config.json

# 6. Test iframe compatibility
#    Open reference/iframe-test.html, update src to your URL, check DevTools Console

# 7. Validate before the demo
python validate_submission.py
```

---

## Validate before committing

```bash
python validate_submission.py
```

Checks that `reference/federation.json` and `reference/theme.config.json` are complete and valid.
A passing validator is required before your live demo.

The pre-commit hook runs this automatically when you `git commit`.

---

## Submit

```bash
git add .
git commit -m "Team <your-team-name>: Robotics Strand final submission"
git push origin your-team-name
```

Then open a Pull Request: `your-team-name` → `robotic`
