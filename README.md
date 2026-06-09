# Robotics (SONAIR) Strand — Can Your Robotics Evidence Be Trusted Beyond the Lab?

**MultimodalAI'26 Hackathon · 10 June 2026**

> **No prior robotics or web development expertise required.**
> You will receive a real dataset, a working main portal to plug into, and support from problem holders throughout the day. Your job is to build something that represents your lab and contributes to a shared national network. We handle the infrastructure. You handle the content and the analysis.

Read **[STRAND_GUIDE.md](STRAND_GUIDE.md)** for the full challenge brief, track roles, deliverables, and judging criteria. If you are short on time, start with Section 10 (Your First 30 Minutes).

---

## What This Strand Is About

SONAIR is a proposed national benchmark for the robotics simulation-to-real (sim2real) gap. Each team builds a **Campus Sub-Portal** that plugs into the SONAIR network — a publicly accessible website representing your university or lab, connected to a shared national portal via a standard federation protocol.

You will also be given a real teleoperation dataset from the UCL–Nottingham UR5e robot experiment. Your task: create plots, explore timing and latency patterns, and propose a metric that could help describe the sim2real gap.

---

## What Is in This Repository

```
robotic/
├── README.md                     ← you are here
├── STRAND_GUIDE.md               ← full task description, roles, judging criteria
├── validate_submission.py        ← pre-submission validator (run before demo)
├── .pre-commit-config.yaml       ← pre-commit hook configuration
├── reference/
│   ├── federation.json           — federation manifest template (item B)
│   ├── theme.config.json         — theme configuration template (item C)
│   └── iframe-test.html          — iframe compatibility test page (item D)
├── sub-portals/                  ← your campus sub-portal files go here
├── data/                         ← dataset (released at hackathon start)
│   └── README.md                 — dataset documentation
└── demo/                         ← reference examples
```

> Your `node.id` in `reference/federation.json` must match your branch name exactly.

---

## Quick Start

```bash
# Clone this branch only
git clone --branch robotic --single-branch https://github.com/omaib/mmai26-hackathon
cd mmai26-hackathon

# Create your team branch immediately — all your work goes here
git checkout -b your-team-name

# Install pre-commit hooks (runs the validator automatically on each commit)
pip install pre-commit
pre-commit install

# Deploy your sub-portal (GitHub Pages recommended)
#   Enable: Settings → Pages → Source: main branch → /sub-portals/your-team-name
#   Confirm the live URL loads in an incognito browser before filling in node.url

# Fill in reference/federation.json and reference/theme.config.json

# Test iframe compatibility
#   Open reference/iframe-test.html, update src to your URL, check DevTools Console

# Validate before the demo
python validate_submission.py
```

**Do not commit directly to the `robotic` branch.** All your work goes on your team branch.

---

## What You Submit

| Item | File / Location | Description |
|---|---|---|
| **A** | `sub-portals/your-team-name/` | Campus Sub-Portal — live, publicly accessible HTTPS website |
| **B** | `reference/federation.json` | Federation manifest — all 10 fields filled with real values |
| **C** | `reference/theme.config.json` | Theme config — portal applies `primary_color` as a CSS variable |
| **D** | *(verified via iframe-test.html)* | Iframe compatibility — no console errors |
| **E** | *(embedded in sub-portal)* | Robot Data Dashboard — RTT plot, latency histogram, written interpretation |

Run `python validate_submission.py` before committing — it checks that `federation.json` and `theme.config.json` are complete and valid.

---

## Pre-commit Hooks

```bash
pip install pre-commit
pre-commit install
# Hooks run automatically on every commit.
# To run manually:
pre-commit run --all-files
```

---

## How to Submit

```bash
git add .
git commit -m "Team <your-team-name>: Robotics Strand final submission"
git push origin your-team-name
```

Then open a Pull Request on GitHub: `your-team-name → robotic`
Title: `"Team <your-team-name> — Robotics Strand Submission"`

**Final submission deadline: before 09:30 on 11 June.** Do not push directly to the `robotic` branch.

---

## Judging Criteria

| Criterion | Weight | What it means |
|---|---|---|
| **Sub-portal creativity and clarity** | 25% | A clear, engaging portal that represents a lab or institution well — purposeful, not a generic template |
| **SONAIR federation readiness** | 15% | A working deployed portal, valid `federation.json`, and basic compatibility with the SONAIR federation concept |
| **Data analysis and plots** | 25% | Meaningful plots from the UR robot teleoperation dataset, with sensible handling of timestamps, latency, delay, or synchronisation |
| **Proposed metric** | 15% | A clear and defensible metric that could help describe latency, synchronisation, or sim-to-real behaviour |
| **Final presentation and GenAI use** | 20% | Clear explanation of the portal, data findings, metric, design choices, and limitations |

---

## What You Will Gain

- **Explore real-world challenges in trustworthy multimodal AI.**
- **Produce research tools and papers via collaborative work.** Our previous sprint produced a [perspective paper in *Nature Machine Intelligence*](https://www.nature.com/articles/s42256-025-01116-5) — strong deployment-centric findings from this hackathon will be considered for contributions to the OMAIB benchmark and future publications.
- **Build ideas that funders and users can understand and trust.**
- **Experience the shaping of future AI assurance by regulations.**
- **Win Amazon voucher prizes.**

---

## Support

| Need | Who to ask |
|---|---|
| Understanding the dataset or teleoperation context | Problem holders (present throughout the day) |
| Sim2real gap, RTT, or latency concepts | Problem holders |
| `federation.json` schema or validation | Technical support desk |
| Iframe embedding or HTTPS deployment | Technical support desk |
| Scoping or redefining your challenge | Problem holders |

> **You are not expected to know everything going in. Ask early, ask often.**
