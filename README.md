# MultimodalAI'26 Hackathon

**10 June 2026 · London, UK**
*Teaching Space 4, Room 301 · One Pool Street · London · E20 2AF*
*Co-located with the Fourth Workshop on Multimodal AI 2026 · 11–12 June 2026*

> **"Prove It — Building Evidence for Trustworthy Multimodal AI Deployment"**

These strands are designed to foster creativity and make the hackathon genuinely enjoyable for every participant, whilst keeping sight of a serious objective: trustworthy multimodal AI deployment.

---

## The Challenge

AI systems are being deployed in ICUs, social housing, and robotic platforms — but can the people who depend on them actually trust them? Trust has to be earned with evidence, not assumed.

Each team produces two things: a solution they choose to build, and a structured set of strand-specific evidence deliverables. The dataset provided for each strand is the foundation for both. The best entries will not just measure performance — they will find the failures, name the risks, and make the case for what needs to change before deployment.

---

## The Three Strands

Choose one strand for your whole team. Each strand has a dataset, a set of challenge options, and three track roles that divide the work across your team.

---

### Clinical Strand
**Challenge:** Can you trust an AI in the ICU?

It is 3 a.m. on an intensive care unit. A nurse is managing eight patients simultaneously. A patient in bed 6 has been stable for hours — but in the next six hours, they will deteriorate sharply. Their heart rate is slightly elevated. Their lactate is creeping up. A brief note from the evening team mentioned "looks a bit off." None of these signals, alone, would trigger an alarm.

An AI system reviews all 5,000 patients and flags the ones it predicts will deteriorate in the next 24 hours. The nurse sees the alert and acts. Or the AI misses the patient entirely, and the nurse doesn't know to look twice.

Each team builds a solution grounded in the clinical dataset and produces a set of evidence deliverables that a hospital safety committee could act on. The problem is defined. The dataset is provided. The output templates are given to you — **you fill them in based on what you find.** What you bring is the analysis, the judgement, and the communication.

**Challenge ideas (or define your own grounded in the dataset):**

- **Clinical AI Readiness Decision Support** — an AI-powered tool that helps a hospital decide whether an ICU model is ready for deployment, restricted use, further validation, or rejection.
- **Bedside Alarm Explainability Product** — a product that surfaces plain-language reasoning behind every AI-generated ICU alarm, so clinicians can accept or override with one tap and the rationale is logged. The product must also measure whether AI alerts risk overwhelming clinicians or would meaningfully improve response times.
- **Patient Population Drift Monitor** — a lightweight monitoring service that sends an early-warning signal when the ICU patient population diverges meaningfully from the model's training cohort.

> **Not sure which to pick?** You can also define your own compelling problem grounded in the dataset. Discuss it with a problem holder before committing.

### What You Build
**Core mandatory deliverables (all options):**
- **A. The solution** — a runnable tool with a clear intended user and a working demonstration of its core function. Your team may choose one of the suggested challenge ideas or define your own compelling problem grounded in the dataset.
- **B. OMAIB Pathway Manifest** — `omaib_pathway.json` — a structured JSON manifest containing per-model verdicts and metrics for all the models you used.
- **C. Model Safety Report** — `model_safety_report.json` — a structured JSON report containing the full safety assessment: narrative, subgroup analysis, deployment questions, and option-specific evidence.
- **D. Evidence Dashboard** — five analytical views populated through your chosen tools and workflows: model performance, subgroup equity, explainability, failure mode catalogue, and clinical deployment assessment.
- **E. Option-specific deliverable** — a JSON section (`option_specific`) embedded within item C, with content specific to the challenge idea your team chose.

*Modalities:* vital signs, laboratory results, clinical notes (NLP risk score)

*Track roles:* The Builder · The Evidence Analyst · The Governance Lead

Refer to the clinical strand guide for more information.

---

### Housing Strand
**Challenge:** Can you trust a dataset used for housing decisions?

A council housing team is trying to decide which of its 250 social housing properties should receive a boiler upgrade this winter. They have two years of daily sensor readings — indoor temperature, humidity, CO₂ concentration, ambient sound levels, and smart meter energy consumption — alongside sparse resident comfort survey responses, from a sensor network installed across the estate.

The data looks comprehensive. But a data manager notices something: for 40 of the properties, the CO₂ sensor stopped working for weeks at a time. These properties are not a random sample — they tend to be older, in higher-deprivation areas, and more likely to be in genuine need of an upgrade. The model trained on this dataset will be least reliable for the very households it is most important to get right.

Before anyone uses this dataset to decide which households receive a boiler upgrade, someone must answer a hard question: is this data safe to use?

Each team builds a solution grounded in the housing dataset and produces a set of evidence deliverables that a council, housing association, or social-impact organisation could act on. The problem is defined. The dataset is provided. The output templates are given to you — **you fill them in based on what you find.** What you bring is the analysis, the judgement, and the communication.

**Challenge ideas (or define your own grounded in the dataset):**

- **Cold home intelligence service** — an AI-powered service that ranks properties by cold-risk score for a housing provider's asset management team.
- **Sensor network health and MNAR audit** — an estate-wide sensor health monitor that tracks CO₂ dropout rates per property over time and detects continuous data gaps beyond a configurable threshold, designed for use by a housing data manager.
- **Heating failure prediction and fairness audit** — an AI-powered predictive tool that combines sensor time-series data with property metadata to identify households at imminent risk of heating system failure, with an explainability layer and a fairness check that flags whether high-risk scores are disproportionately concentrated among particular property types.

> **Not sure which to pick?** You can also define your own compelling problem grounded in the dataset. Discuss it with a problem holder before committing.

### What You Build
**Core mandatory deliverables (all options):**
- **A. The solution** — a runnable tool with a clear intended user and a working demonstration of its core function.
- **B. OMAIB Pathway Manifest** — `omaib_pathway.json` — a structured JSON manifest containing per-model verdicts and metrics for all the models you built and evaluated.
- **C. Housing Benchmark Card** — `housing_benchmark_card.json` — a structured JSON report containing the full dataset and model assessment: narrative, subgroup analysis, deployment questions, component verdicts, and option-specific evidence.
- **D. Evidence Dashboard** — five analytical views populated through your chosen tools and workflows: sensor data quality, MNAR analysis, subgroup equity, leakage audit, and dataset audit.
- **E. Option-specific deliverable** — a JSON section (`option_specific`) embedded within item C, with content specific to the challenge idea your team chose.

*Modalities:* IoT sensors (indoor temperature, humidity, CO₂ concentration, ambient noise), smart meter (daily energy consumption kWh), property metadata, resident survey data (sparse)

*Track roles:* The Builder · The Evidence Analyst · The Governance Lead

Refer to the housing strand guide for more information.

---

### Robotics Strand
**Challenge:** Can your robotics evidence be trusted beyond the lab?

A robot lab's findings sit in a silo. They cannot be discovered, verified, or built upon by other universities or industry partners unless they are made accessible in a trusted, structured way. SONAIR is the proposed national federation that changes this. Your job is to build a Campus Sub-Portal that plugs into the SONAIR network and demonstrates how trustworthy robotics evidence can be published and shared.

*Each option also carries its own specific output: a metric proposal page (option 1), an evidence card and governance policy (option 2), or a usability test report (option 3). All must be embedded in or linked from the live sub-portal before the demo session begins.*

**Challenge options — choose one:**
1. **Sim-to-real gap metric design** — Design, implement, and validate a novel metric quantifying the simulation-to-real gap using the UCL–Nottingham UR5e teleoperation dataset, surfaced in the dashboard alongside supporting visualisations and a written metric proposal.
2. **Federated evidence governance** — Treat the federation manifest as a governance document. Design a structured evidence card format for the SONAIR ecosystem, implement evidence cards for the UR5e dataset, and include a written governance policy explaining what your team chose to publish, what to withhold, and why.
3. **Accessible co-creation portal** — Build the most usable, practitioner-ready campus sub-portal on the strand. Prioritise accessibility, conduct a brief usability test with at least two people outside your team, and propose one concrete, implementable improvement on the page.

### What You Build
**Core mandatory deliverables (all options):**
- **Campus Sub-Portal** — publicly accessible at a stable HTTPS URL; institution name and city, lab identity, at least one equipment item or dataset with specific details, and a collaboration contact. Must load without login and must not set X-Frame-Options headers.
- **Federation Manifest** — a valid `federation.json` at the repository root with all 10 required fields, including real institution coordinates (`node.lat`, `node.lon`)
- **Theme Configuration** — a `theme.config.json` with `institution_name`, `node_name`, `city`, `primary_color`, and `logo_url`; the portal must read this file via `fetch()` and apply `primary_color` as a CSS variable
- **Iframe compatibility** — portal loads cleanly inside an `<iframe>` with no X-Frame-Options or Content-Security-Policy frame-ancestors errors in the browser console
- **Robot Data Dashboard** — an RTT time-series plot, a command latency histogram, and a written interpretation on the page, built from the UCL–Nottingham UR5e teleoperation dataset



*Track roles:* The Builder · The Connector · The Data Engineer

Refer to the Robotic strand guide for more information.

---

## Programme — 10 June 2026

| Start | End | Session |
|---|---|---|
| **09:30** | 10:00 | Arrival, registration, and networking |
| **10:00** | 11:00 | Introduction and team formation |
| **11:00** | 12:45 | **Hackathon begins — Phase 1: Building** |
| **12:45** | 14:00 | Team Sharing 1 and lunch break |
| **14:00** | 15:30 | Phase 1 continues — Building |
| **15:30** | 15:45 | Tea and coffee break |
| **15:45** | 17:30 | Phase 2: Evaluation and Reporting — Minimal Viable Submission by 17:00 |
| **17:30** | 18:00 | Team Sharing 2 |

---

| Date | Event |
|---|---|
| **11 June** — MultimodalAI Workshop Day 1 | Final submission (before 09:30) · Demo session & prize presentation |

---

## Quick Start

> **New to this kind of hackathon?** Each strand provides a demo, ready-to-use templates, and problem holders available throughout the day. You do not need to be a domain expert to contribute.

Each strand is on its own branch. Clone only the branch for your strand — you do not need the others.

```bash
# Replace 'clinical' with 'housing' or 'robotics' as appropriate
git clone --branch clinical --single-branch https://github.com/omaib/mmai26-hackathon
cd mmai26-hackathon
# To run the demo
pip install -r requirements.txt
jupyter notebook notebooks/
```

**Immediately after cloning, create your team branch:**

```bash
# Use your team name — lowercase, hyphens instead of spaces, no special characters
git checkout -b your-team-name
```

All your work goes on your team branch. **Do not commit directly to the strand branch.**

Read `STRAND_GUIDE.md` — it explains the task, the data, your track role, and the deliverables you must complete before the demo on 11 June. If you are short on time, start with the **Your First 30 Minutes** section.

---

## How to Submit

Submission is via a **Pull Request** from your team branch to your strand branch on GitHub. This is the official submission record — judges review your PR.

> **First time using Git?** The technical support desk can help you push and open a PR. Ask early — don't leave it to the last 30 minutes.

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

**Your PR must include all mandatory core deliverables for your strand, plus your option-specific output.** Refer to the *What You Build* section for your strand above, and the Strand Guide for full detail.

**Final submission deadline: before 09:30 on 11 June.** Push your code to your GitHub team branch and open the PR before the demo session begins.

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
- Someone comfortable with code and data tooling — the specific language and tools are your team's choice
- Someone with domain interest (clinical, housing, or robotics — you don't need to be an expert)
- Someone who can write a clear, plain-English paragraph

AI coding assistants are allowed and encouraged. You must disclose what you used in your submission PR description — judges ask questions during the demo to verify understanding.

---

## What You Will Gain

- **Explore real-world challenges in trustworthy multimodal AI.**
- **Produce research tools and papers via collaborative work.** Our previous sprint produced a [perspective paper in *Nature Machine Intelligence*](https://www.nature.com/articles/s42256-025-01116-5) — strong deployment-centric findings from this hackathon will be considered for contributions to the OMAIB benchmark and future publications.
- **Build ideas that funders and users can understand and trust.**
- **Experience the shaping of future AI assurance by regulations.**
- **Win Amazon voucher prizes.**

---

## Judging Criteria

The clinical and housing strands are judged on the same criteria. The robotics strand is judged on different criteria — see the Strand Guide on the `robotic` branch.

**Clinical and housing strands:**

| Criterion | Weight | What it means |
|---|---|---|
| **Creativity** | 15% | Original approach with a clear point of view; the solution and evidence framing say something distinctive about the team's perspective and the problem |
| **Evidence quality** | 35% | Are your findings specific and backed by evidence drawn from the data? Did you surface concrete problems or trust gaps — not just describe their possibility? |
| **Clarity** | 25% | Could a non-technical practitioner — a clinician or housing officer — understand and act on your output? |
| **Deployability** | 25% | How close is your deliverable to something the domain team could actually publish, adopt, or act on? |

**Robotics strand:**

| Criterion | Weight | What it means |
|---|---|---|
| **Sub-portal creativity and clarity** | 25% | A clear, engaging portal that represents a lab or institution well — purposeful, not a generic template |
| **SONAIR federation readiness** | 15% | A working deployed portal, valid `federation.json`, and basic compatibility with the SONAIR federation concept |
| **Data analysis and plots** | 25% | Meaningful plots from the UR robot teleoperation dataset, with sensible handling of timestamps, latency, delay, or synchronisation |
| **Proposed metric** | 15% | A clear and defensible metric that could help describe latency, synchronisation, or sim-to-real behaviour |
| **Final presentation and GenAI use** | 20% | Clear explanation of the portal, data findings, metric, design choices, and limitations |

Judges will ask questions during the demo session. Your team needs to understand what you built and why you made the decisions you made.

---

## Prizes

The winning team receives **Amazon vouchers**, announced and awarded at the MultimodalAI'26 Workshop on 11 June.

Three teams will be recognised:

- 🥇 **Promising Benchmark Award** — the submission most likely to become a lasting benchmark contribution
- 💡 **Best Multimodal Idea** — the most insightful finding across modalities
- 🎤 **Best Demo** — the clearest, most practitioner-ready presentation

---

## What to Bring

- Bring a laptop with **Python 3.11+** installed.
- Install any IDE or code editor of your choice.
- Create a **GitHub account** if you do not already have one.
- Your team (or arrive solo — team formation time is built into the programme)

---

## Frequently Asked Questions

For more information, visit: [UK Open Multimodal AI Network | MultimodalAI'26 Hackathon](https://multimodalai.github.io/multimodalai26/hackathon/#frequently_asked_questions)

---

## Questions and Support

| Need | Who to ask |
|---|---|
| Clinical, housing, or robotics domain questions | Problem holders (present throughout the day) |
| JSON templates, validators, or pre-commit hooks | Technical support desk |
| Scoping or redefining your challenge | Problem holders |
| Git, GitHub, or submission process | Technical support desk |

> **You are not expected to know everything going in. Ask early, ask often.**

**Email: multimodalai26-group@sheffield.ac.uk**

*OMAIB — Open Multimodal AI Benchmarks*
