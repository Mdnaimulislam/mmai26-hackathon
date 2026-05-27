# MultimodalAI'26 Hackathon

**10 June 2026 · London, UK**
*Teaching Space 4, Room 301 · One Pool Street · London · E20 2AF*
*Co-located with the Fourth Workshop on Multimodal AI 2026 · 11–12 June 2026*

> **"Prove It — Building Evidence for Trustworthy Multimodal AI Deployment"**

---

## The Challenge

AI systems are being deployed in ICUs, social housing, and robotic platforms — but can the people who depend on them actually trust them? Trust has to be earned with evidence, not assumed.

This is a **deployment-centric** hackathon. Each team produces two things: a solution they choose to build, and a structured set of strand-specific evidence deliverables. The dataset provided for each strand is the foundation for both. The best entries will not just measure performance — they will find the failures, name the risks, and make the case for what needs to change before deployment.

---

## The Three Strands

Choose one strand for your whole team. Each strand has a dataset, a set of challenge options, and three track roles that divide the work across your team.

---

### Clinical Strand
**Challenge:** Can you trust an AI in the ICU?

It is 3 a.m. on an intensive care unit. A nurse is managing eight patients simultaneously. A patient in bed 6 has been stable for hours — but in the next six hours, they will deteriorate sharply. Their heart rate is slightly elevated. Their lactate is creeping up. A brief note from the evening team mentioned "looks a bit off." None of these signals, alone, would trigger an alarm.

An AI system reviews all 5,000 patients and flags the ones it predicts will deteriorate in the next 24 hours. The nurse sees the alert and acts. Or the AI misses the patient entirely, and the nurse doesn't know to look twice.

Each team builds a solution grounded in the clinical dataset and produces a structured set of evidence deliverables that a clinical governance board could act on. The problem is defined, the dataset is provided, and the output format is specified — but what you build on top, and how you communicate what you find, is entirely your team's.

**Suggested challenge ideas (or define your own grounded in the dataset):**

- **Clinical AI readiness decision support** — an AI-powered solution that helps a hospital decide whether an ICU AI model is ready for deployment, restricted use, further validation, or rejection.
- **Bedside alarm explainability product** — a product with a user interface that surfaces plain-language reasoning behind every AI-generated ICU alarm, so clinicians can accept or override with one tap and the rationale is logged. The product must also measure whether AI alerts risk overwhelming clinicians or would meaningfully improve response times.
- **Patient population drift monitor** — a lightweight monitoring service that continuously compares the incoming patient population against the model's training cohort and sends an early-warning signal when the ICU population diverges meaningfully.


### What You Build
- **A. The solution** — a runnable tool with a clear intended user and a working demonstration of its core function. Your team may choose one of the suggested challenge ideas or define your own compelling problem grounded in the dataset.
- **B. OMAIB Pathway Manifest** — `omaib_pathway.json` — a structured JSON manifest containing per-model verdicts and metrics for all the models you used.
- **C. Model Safety Report** — `model_safety_report.json` — a structured JSON report containing the full safety assessment: narrative, subgroup analysis, deployment questions, and option-specific evidence.
- **D. Evidence Dashboard** — five analytical views populated through your chosen tools and workflows: model performance, subgroup equity, explainability, failure mode catalogue, and clinical deployment assessment.
- **E. Option-specific deliverable** — a JSON section (`option_specific`) embedded within item C, with content specific to the challenge idea your team chose.

*Modalities:* vital signs, laboratory results, clinical notes (NLP risk score)

*Track roles:* The Builder · The Evidence Analyst · The Governance Lead

---

### Housing Strand
**Challenge:** Can you trust a dataset used for housing decisions?

A council housing team is trying to decide which of its 250 social housing properties should receive a boiler upgrade this winter. They have two years of daily sensor readings — indoor temperature, humidity, CO₂ concentration, ambient sound levels, and smart meter energy consumption — alongside sparse resident comfort survey responses, from a sensor network installed across the estate.

The data looks comprehensive. But a data manager notices something: for 40 of the properties, the CO₂ sensor stopped working for weeks at a time. These properties are not a random sample — they tend to be older, in higher-deprivation areas, and more likely to be in genuine need of an upgrade. The model trained on this dataset will be least reliable for the very households it is most important to get right.

Before anyone uses this dataset to decide which households receive a boiler upgrade, someone must answer a hard question: is this data safe to use?

Each team builds a solution grounded in the housing dataset and produces a structured set of evidence deliverables that a council, housing association, or social-impact organisation could act on. The problem is defined, the dataset is provided, and the output format is specified — but what you build on top, and how you communicate what you find, is entirely your team's.

**Suggested challenge ideas (or define your own grounded in the dataset):**

- **Cold home intelligence service** — an AI-powered service that ranks properties by cold-risk score for a housing provider's asset management team.
- **Sensor network health and MNAR audit** — an estate-wide sensor health monitor that tracks CO₂ dropout rates per property over time and detects continuous data gaps beyond a configurable threshold, designed for use by a housing data manager.
- **Heating failure prediction and fairness audit** — an AI-powered predictive tool that combines sensor time-series data with property metadata to identify households at imminent risk of heating system failure, with an explainability layer and a fairness check that flags whether high-risk scores are disproportionately concentrated among particular property types.

### What You Build

- **A. The solution** — a runnable tool with a clear intended user and a working demonstration of its core function.
- **B. OMAIB Pathway Manifest** — `omaib_pathway.json` — a structured JSON manifest containing per-model verdicts and metrics for all the models you built and evaluated.
- **C. Housing Benchmark Card** — `housing_benchmark_card.json` — a structured JSON report containing the full dataset and model assessment: narrative, subgroup analysis, deployment questions, component verdicts, and option-specific evidence.
- **D. Evidence Dashboard** — five analytical views populated through your chosen tools and workflows: sensor data quality, MNAR analysis, subgroup equity, leakage audit, and dataset audit.
- **E. Option-specific deliverable** — a JSON section (`option_specific`) embedded within item C, with content specific to the challenge idea your team chose.

*Modalities:* IoT sensors (indoor temperature, humidity, CO₂ concentration, ambient noise), smart meter (daily energy consumption kWh), property metadata, resident survey data (sparse)

*Track roles:* The Builder · The Evidence Analyst · The Governance Lead

---

### Robotics Strand
**Challenge:** Can your robotics evidence be trusted beyond the lab?

A robot lab's findings sit in a silo. They cannot be discovered, verified, or built upon by other universities or industry partners unless they are made accessible in a trusted, structured way. SONAIR is the proposed national federation that changes this. Your job is to build a Campus Sub-Portal that plugs into the SONAIR network and demonstrates how trustworthy robotics evidence can be published and shared.

*Each option also carries its own specific output: a metric proposal page (option 1), an evidence card and governance policy (option 2), or a usability test report (option 3). All must be embedded in or linked from the live sub-portal before the demo session begins.*

**Challenge options — choose one:**
1. **Sim-to-real gap metric design** — Design, implement, and validate a novel metric quantifying the simulation-to-real gap using the UCL–Nottingham UR5e teleoperation dataset, surfaced in the dashboard alongside supporting visualisations and a written metric proposal.
2. **Federated evidence governance** — Treat the federation manifest as a governance document. Design a structured evidence card format for the SONAIR ecosystem, implement at least one evidence card for the UR5e dataset, and include a written governance policy explaining what your team chose to publish, what to withhold, and why.
3. **Accessible co-creation portal** — Build the most usable, practitioner-ready campus sub-portal on the strand. Prioritise accessibility, conduct a brief usability test with at least two people outside your team, and propose one concrete, implementable improvement on the page.

**Core mandatory deliverables (all options):**
- **Campus Sub-Portal** — publicly accessible at a stable HTTPS URL; institution name and city, lab identity, at least one equipment item or dataset with specific details, and a collaboration contact. Must load without login and must not set X-Frame-Options headers.
- **Federation Manifest** — a valid `federation.json` at the repository root with all 10 required fields, including real institution coordinates (`node.lat`, `node.lon`)
- **Theme Configuration** — a `theme.config.json` with `institution_name`, `node_name`, `city`, `primary_color`, and `logo_url`; the portal must read this file via `fetch()` and apply `primary_color` as a CSS variable
- **Iframe compatibility** — portal loads cleanly inside an `<iframe>` with no X-Frame-Options or Content-Security-Policy frame-ancestors errors in the browser console
- **Robot Data Dashboard** — an RTT time-series plot, a command latency histogram, and a written interpretation on the page, built from the UCL–Nottingham UR5e teleoperation dataset


*Modalities:* lab capability metadata, robot dataset registries, federation manifests (JSON), institution profiles, web configuration

*Track roles:* The Builder · The Connector · The Data Engineer

---

## Programme — 10 June 2026

| Start | End | Session |
|---|---|---|
| **09:30** | 10:00 | Arrival, registration, refreshments, and networking |
| **10:00** | 10:20 | Welcome and scene-setting — why this hackathon, what OMAIB is, what the strands need |
| **10:20** | 10:30 | Team formation and strand selection — participants select a strand and find their table |
| **10:30** | 11:00 | **Hackathon begins (Phase 1)** — Q&A and starter kit walkthrough |
| **11:00** | 13:00 | Phase 2: Build — teams split by track roles |
| **13:00** | 14:00 | Lunch break |
| **14:00** | 16:00 | Phase 2 / Phase 3: building continues and teams converge on the final report |
| **16:00** | 16:30 | Tea and coffee break |
| **16:30** | 18:00 | Final push — packaging, submission forms, demo prep |
| **18:00+** | — | Submission — open your PR against your strand branch |

---

| Date | Event |
|---|---|
| **11 June** — MultimodalAI Workshop Day 1 | Winner announcement  & Prize awarded |

---

## Quick Start

Each strand is on its own branch. Clone only the branch for your strand — you do not need the others.

```bash
# Replace 'clinical' with 'housing' or 'robotics' as appropriate
git clone --branch clinical --single-branch https://github.com/omaib/mmai26-hackathon
cd mmai26-hackathon
# To run the demo
pip install -r requirements.txt
jupyter notebook notebooks/
```

> **Robotics strand only:** the deliverable is a web portal, not a Jupyter notebook. After cloning, open `index.html` and the accompanying JSON config files. No `pip install` is required unless you are building a Python-backed dashboard component.

**Immediately after cloning, create your team branch:**

```bash
# Use your team name — lowercase, hyphens instead of spaces, no special characters
git checkout -b your-team-name
```

All your work goes on your team branch. **Do not commit directly to the strand branch.**

Read `STRAND_GUIDE.md` first — it explains the task, the data, your track role, and the deliverables you must complete before the demo.

---

## How to Submit

Submission is via a **Pull Request** from your team branch to your strand branch on GitHub. This is the official submission record — judges review your PR.

```bash
# Step 1 — Commit your final work
git add .
git commit -m "Team <your-team-name>: final submission"

# Step 2 — Push your team branch to the remote
git push origin your-team-name

# Step 3 — Open a Pull Request on GitHub
# Go to: https://github.com/omaib/mmai26-hackathon
# PR: your-team-name  →  clinical   (or housing / robotics)
# Title: "Team <your-team-name> — <Strand> Strand Submission"
```

**Your PR must include all mandatory core deliverables for your strand, plus your option-specific output.**

For the clinical and housing strands this includes the completed JSON output file, all completed notebooks (run top to bottom, outputs saved), and the exported report. For the robotics strand this includes the live portal URL, `federation.json`, `theme.config.json`, and any option-specific page or document embedded in or linked from the portal.

**Submission window: 18:00–23:59 on 10 June.** Push your code to your GitHub team branch and open the PR during this window.

---

## Pre-commit Hooks

Clinical and housing strand repositories use pre-commit hooks to validate submission files and enforce code quality.

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files  # optional: run manually on all files
```

Pre-commit hooks run automatically on every commit.

---

## Team Structure

**Recommended team size:** 2–4 people.

Each strand is designed for a team of 2–4, with parallel track roles during the build phase and a full-team convergence for the final report and demo. A team of 2 is tight but achievable; 5 or more leads to idle members during the analysis and interpretation steps.

**Ideal skill mix** — you need at least one person from each of these buckets:
- Someone comfortable with Python and pandas — or HTML/CSS/JavaScript for the robotics strand
- Someone with domain interest (clinical, housing, or robotics — you don't need to be an expert)
- Someone who can write a clear, plain-English paragraph

**AI coding assistants** (GitHub Copilot, Claude, ChatGPT) are allowed and encouraged. You must disclose what you used in your submission PR description — judges ask questions during the demo to verify understanding.

---

## Who Can Join

The hackathon is open to **registered MultimodalAI'26 workshop attendees**. Please complete the hackathon registration form to secure your place. Registration closes **4 June 2026**.

**Eligible participants include:**
- Graduate students (MSc, MEng, PhD) attending the workshop
- Postdoctoral researchers and research fellows
- University academic and research staff
- Industry researchers, engineers, and practitioners
- Clinicians, housing officers, safety inspectors, and domain experts — no prior machine learning experience required if teaming with technical members

**Cross-disciplinary and cross-institution teams are strongly encouraged.** The judging explicitly rewards teams that combine domain expertise with technical skill.

Solo participants are welcome — team formation at 10:20 is for exactly this.

---

## What You Will Gain

- **Explore real-world challenges in trustworthy multimodal AI.**
- **Produce research tools and papers via collaborative work.** Our previous sprint produced a [perspective paper in *Nature Machine Intelligence*](https://www.nature.com/articles/s42256-025-01116-5) — strong deployment-centric findings from this hackathon will be considered for contributions to the OMAIB benchmark and future publications.
- **Build ideas that funders and users can understand and trust.**
- **Experience the shaping of future AI assurance by regulations.**
- **Win Amazon voucher prizes.**

---

## Judging Criteria

All strands are judged on the same three criteria:

| Criterion | Weight | What it means |
|---|---|---|
| **Creativity** | 15% | Original approach with a clear point of view; the solution and evidence framing say something distinctive about the team's perspective and the clinical problem |
| **Evidence quality** | 35% | Are your findings specific and backed by evidence drawn from the data? Did you surface concrete problems or trust gaps — not just describe their possibility? |
| **Clarity** | 25% | Could a non-technical practitioner — a clinician, housing officer, or robotics researcher — understand and act on your output? |
| **Deployability** | 25% | How close is your deliverable to something the domain team could actually publish, adopt, or act on? |

Judges will ask questions during the demo session. Your team needs to understand what you built and why you made the decisions you made — not just show a working notebook.

---

## Prizes

The winning team receives **Amazon vouchers**, announced and awarded at the MultimodalAI'26 Workshop on 11 June.

Three teams will be recognised:

- 🥇 **Promising Benchmark Award** — the submission most likely to become a lasting benchmark contribution
- 💡 **Best Multimodal Idea** — the most insightful finding across modalities
- 🎤 **Best Demo** — the clearest, most practitioner-ready presentation

---

## What to Bring

- A laptop with **Python 3.11+** installed and a Jupyter Notebook-supported IDE (VS Code with the Jupyter extension, JupyterLab, or PyCharm)
- A **GitHub account** — you will need to push your team branch and open a PR during the submission window (18:00–23:59)
- Your team (or arrive solo — team formation time is built into the programme)

---

## Frequently Asked Questions

**Do I need to be an AI expert to participate?**
No. Every strand is designed for cross-disciplinary teams. If you understand the domain — clinical, housing, or robotics — your contribution is as valuable as the person writing Python.

**Do I need to come with a team?**
No. Solo participants are welcome. Team formation runs from 10:20 to 10:30 on the day.

**What if I have never used Jupyter notebooks before?**
Install VS Code with the Jupyter extension, or use JupyterLab — both are free and work in a few minutes. The notebooks guide you step by step. If you can read Python and run cells, you have enough.

**Can I use AI coding assistants?**
Yes, and we encourage it. You must disclose what you used in your PR description — judges ask questions during the demo to verify understanding.

**What is the team branch name convention?**
Use your team name in lowercase with hyphens instead of spaces — e.g., `team-alpha`, `cardiff-med`, `ucl-robotics-2`. No special characters. The branch name is how judges identify your submission.

**How do we submit?**
Push your team branch to GitHub and open a Pull Request against your strand branch (e.g., `team-alpha` → `clinical`). The submission window is **18:00–23:59 on 10 June**.

**Will my work be published or used elsewhere?**
Strong deployment-centric findings from this hackathon will be considered for contributions to the OMAIB benchmark and future publications. Our previous sprint produced a [perspective paper in *Nature Machine Intelligence*](https://www.nature.com/articles/s42256-025-01116-5) — evaluation work done here has a direct path to publication.

**What should I prepare before the day?**
On 4 June, your strand guide and starter kit will be sent to you. Open the notebook (or portal files for robotics) in your IDE, confirm everything loads, and run through the starter so you are ready on the day.

**How do I access the strand repository?**
24 hours before the start time, you will be given access to the GitHub repository. Create a GitHub account if you do not have one. Clone your strand branch, confirm Python 3.11+ is installed, and agree a team name — you will need it for your branch on the day.

---

## Questions

**multimodalai26-group@sheffield.ac.uk**

*OMAIB — Open Multimodal AI Benchmarks*
