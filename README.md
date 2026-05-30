# Robotics Strand — SONAIR: Can Your Robotics Evidence Be Trusted Beyond the Lab?

**MultimodalAI'26 Hackathon · 10 June 2026**

---

## Read this first

Read **[STRAND_GUIDE.md](STRAND_GUIDE.md)** for the full challenge brief, track roles, deliverables, and what your team must produce.

---

## What is provided

| Path | Contents |
|---|---|
| `federation.json` | Federation manifest template — fill in your team's institution details |
| `theme.config.json` | Theme configuration template — fill in your brand colours and logo |
| `iframe-test.html` | Iframe compatibility test — update `src` to your deployed URL |
| `sub-portals/` | Directory for your campus sub-portal files |
| `data/` | Dataset released at hackathon start — see `data/README.md` |
| `validate_submission.py` | Pre-submission validator — run before your demo |

---

## Create your team branch immediately after cloning

```bash
git checkout -b your-team-name
```

All your work goes on your team branch. **Do not commit directly to the robotic branch.**

---

## Quick start

```bash
# 1. Fork and clone this repository
# 2. Create your team branch
git checkout -b your-team-name

# 3. Deploy your sub-portal (GitHub Pages recommended)
#    Enable: Settings → Pages → Source: main branch → root or /docs

# 4. Install data analysis dependencies
pip install -r requirements.txt

# 5. Validate your submission before the demo
python validate_submission.py
```

---

## Validate before committing

```bash
python validate_submission.py
```

Checks that `federation.json` and `theme.config.json` are complete and valid.
A passing validator is required before your live demo.

---

## Submit

```bash
git add .
git commit -m "Team <your-team-name>: Robotics Strand final submission"
git push origin your-team-name
```

Then open a Pull Request: `your-team-name` → `robotic`
