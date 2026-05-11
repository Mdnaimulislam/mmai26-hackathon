# MultimodalAI’26 Hackathon

**10 June 2026 · London, UK**
*Teaching Space 4, Room 301 · One Pool Street · London · E20 2AF*
*Co-located with the Fourth Workshop on Multimodal AI 2026 · 11–12 June 2026*

> **"Prove It — Building Evidence for Trustworthy Multimodal AI"**

---

## The Challenge

Multimodal AI systems are being deployed in hospitals, homes, vehicles, and robotic platforms. But are they safe? Are they fair? Can the people who depend on them actually trust them?

This hackathon asks you to answer that question — with evidence.

Choose a strand, build a tool that evaluates or explains a multimodal AI system, and produce a structured output a real practitioner could act on. The best entries won't just measure performance — they will find the failures, name the risks, and make the case for what needs to change before deployment.

---

## The Five Strands

Choose one strand for your whole team. Each strand has a dataset, guided notebooks, and three track roles that divide the work across your team.

---

### Automotive Strand
**Challenge:** Can you trust an AI dashcam?

Three AI models classify dashcam incidents as high-risk or low-risk across a fleet of 600 UK vehicles. Before any model is trusted to route incidents to a human reviewer — or clear them without review — your team must evaluate whether it is safe, reliable, and honest about where it fails.

*Modalities:* vehicle telemetry (speed, braking, lateral acceleration), dashcam footage risk scores, ADAS flags, audio events
*Final deliverable:* Model Safety Report — APPROVE / CONDITIONAL / NOT APPROVED per model
*Track roles:* The Explainer · The Failure Hunter · The Gatekeeper

---

### Clinical Strand
**Challenge:** Can you trust an AI in the ICU?

Three AI models predict which hospital patients will deteriorate in the next 24 hours. Before any of them are deployed, someone needs to verify they are safe, fair, and honest about what they don't know.

*Modalities:* vital signs, laboratory results, clinical notes (NLP risk score)
*Final deliverable:* Model Safety Report — APPROVE / CONDITIONAL / NOT APPROVED per model
*Track roles:* The Explainer · The Failure Hunter · The Gatekeeper

---

### Housing Strand
**Challenge:** Is this dataset good enough to build a benchmark on?

A smart sensor network in 120 social housing properties. Six months of readings. Broken sensors, drifting timestamps, and surveys that were never returned. A forecasting model that performs well on average — but not for everyone.

*Modalities:* smart meter time-series, IoT sensors (temperature, CO₂, noise), resident surveys
*Final deliverable:* Housing Benchmark Card — READY / CONDITIONAL / NOT READY
*Track roles:* The Sensor Inspector · The Split Builder · The Equity Analyst

---

### Robotics Strand
**Challenge:** The robot passed every test in simulation. Then it met reality.

80 robot runs performed in simulation, then repeated on a real robot. The simulation achieves 91% task success. The real robot achieves 59%. Your job is to quantify what changed, find the load-bearing sensors, and build the gate that decides which runs are safe to approve.

*Modalities:* IMU time-series (6-axis), camera labels, audio, safety flags
*Final deliverable:* SONAIR Deployment Gate — APPROVED / CONDITIONAL / BLOCKED per run
*Track roles:* The Transfer Analyst · The Stress Tester · The Deployment Gatekeeper

---

### Open Strand
**Challenge:** Where should multimodal AI be trusted — and how would you prove it?

Choose your own domain. Any real-world application where an AI system uses more than one type of data. Build a tool that evaluates, explains, or benchmarks it.

*Modalities:* your choice
*Final deliverable:* structured evaluation output + 3-paragraph narrative
*Directions:* The Watchdog · The Translator · The Field Researcher

---

## Programme — 10 June 2026

| Start | End | Session |
|---|---|---|
| **09:30** | 10:00 | Arrival and registration — tea, coffee |
| **10:00** | 10:20 | Welcome and scene-setting — why this hackathon, what OMAIB is, what each strand needs |
| **10:20** | 10:30 | Team formation and strand selection — participants choose a strand and find their table |
| **10:30** | 11:00 | **Hackathon begins** — Q&A and starter kit walkthrough, brief demo of a worked OMAIB pathway example |
| **11:00** | 13:00 | Phase 2: Build — teams split by track roles |
| **13:00** | 14:00 | Lunch break |
| **14:00** | 16:00 | Phase 2 / Phase 3: building continues and teams converge |
| **16:00** | 16:30 | Afternoon tea break |
| **16:30** | 17:00 | Final push — packaging, submission forms, demo prep |
| **17:00** | 18:00 | **Demo session** |

---

| Date | Event |
|---|---|
| **11 June** — MultimodalAI Workshop Day 1 | Winner announcement |
| **12 June** — MultimodalAI Workshop Day 2 *(last day)* | Prize winner announcement |

---

## Team Structure

**Recommended team size:** 3–5 people.

Each strand is designed for a team of 3–5, with 2–3 parallel track roles in Phase 2 and a full-team convergence in Phase 3. A team of 3 is tight but achievable; 6 or more leads to idle members during the analysis and interpretation steps.

**Ideal skill mix** — you need at least one person from each of these buckets:
- Someone comfortable with Python and pandas
- Someone with domain interest (clinical, housing, robotics, or automotive — you don't need to be an expert)
- Someone who can write a clear, plain-English paragraph

**AI coding assistants** (GitHub Copilot, Claude, ChatGPT) are allowed and encouraged. Each strand's README explains the best places to use them. Disclose what you used in your submission form — judges will ask questions during the demo.

---

## Who Can Join

The hackathon is open to **registered MultimodalAI'26 workshop attendees**. No separate application — workshop registration includes hackathon access.

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

- **Practical skills** in multimodal AI evaluation, fairness auditing, and model governance — the skills that separate a model builder from a responsible AI practitioner
- **A contribution to OMAIB** — the Open Multimodal AI Benchmarks initiative. Strong submissions may be incorporated into the benchmark registry, with team attribution
- **A portfolio artefact** — your Model Safety Report, Housing Benchmark Card, Deployment Gate, or Incident Safety Card is a structured, publishable output you can cite and share
- **Cross-disciplinary network** — the participant mix of clinicians, engineers, data scientists, and policy people is the point, not a side effect
- **Recognition** — winning teams are announced at the MultimodalAI'26 Workshop and prizes are awarded on the final day

---

## Judging Criteria

All strands are judged on the same three criteria:

| Criterion | What it means |
|---|---|
| **Evidence quality** | Are your findings quantified and specific? Did you find real failure modes, not just describe the possibility of them? |
| **Clarity** | Could a non-technical practitioner — a clinician, housing officer, or engineer — understand and act on your output? |
| **Deployability** | How close is your deliverable to something the domain team could actually publish, use, or submit to a benchmark registry? |

Judges will ask questions. Your team needs to understand what you built and why you made the decisions you made — not just show a working notebook.

---

## Prizes

The winning team will be awarded a **£200 Amazon voucher**.

Winners will be announced at the MultimodalAI'26 Workshop on 11 June. The prize will be awarded on 12 June (Workshop Day 2).

---

## What to Bring

- A laptop (one per team is sufficient; more is better for parallel work)
- A GitHub account (you will need to make your code public before the demo session)
- Python 3.10+ installed, or a Google account for Colab
- Your team (or arrive solo — team formation time is built into the programme)

---

## Quick Start

Each strand is on its own branch. Clone only the branch for your strand — you do not need the others.

```bash
# Clinical strand
git clone --branch clinical --single-branch https://github.com/omaib/mmai26-hackathon
cd mmai26-hackathon
pip install -r requirements.txt
jupyter notebook notebooks/01_explore_and_train.ipynb

# Automotive strand
git clone --branch automotive --single-branch https://github.com/omaib/mmai26-hackathon
cd mmai26-hackathon
pip install -r requirements.txt
jupyter notebook notebooks/01_explore_and_train.ipynb
```

Or open any notebook directly in Google Colab — no local installation needed.

Read `STRAND_GUIDE.md` first — it explains the task, the data, your role, and the questionnaire you must complete before generating the final report.

---

## Frequently Asked Questions

**Do I need to be an AI expert to participate?**
No. Every strand is designed for cross-disciplinary teams. If you understand the domain — clinical, housing, robotics, or automotive — your contribution is as valuable as the person writing Python. The skill mix that wins is not the deepest ML knowledge; it is the best combination of technical analysis and plain-English reasoning.

**Do I need to come with a team?**
No. Solo participants are welcome. Team formation runs from 10:20 to 10:30 on the day. Come with your interests and strand preference in mind.

**What if I have never used Jupyter notebooks before?**
Each strand opens in Google Colab with one click — no installation, no setup. The notebooks guide you step by step. If you can read Python and run cells, you have enough.

**Can I use AI coding assistants?**
Yes, and we encourage it. GitHub Copilot, Claude, and ChatGPT are all permitted. The Track A report generators across several strands are natural LLM use cases. You must disclose what you used in your submission form — judges ask questions during the demo to verify understanding.

**Do I need to bring my own data?**
Only for the Open Strand. All other strands provide synthetic datasets in the starter kit. Open Strand participants may bring their own data, use any public dataset, or work with generated examples.

**Is the hackathon only for MultimodalAI'26 workshop attendees?**
No. Hackathon-only registration is available and does not require workshop attendance. Workshop attendees are automatically eligible.

**Will my work be published or used elsewhere?**
Strong submissions may be incorporated into the OMAIB benchmark registry with full team attribution. You retain ownership of your work under CC BY 4.0 or Apache 2.0.

**What should I prepare before the day?**
Read your strand's README (15 minutes). Install the requirements or open the notebook in Colab to confirm it loads. Have a GitHub account ready. Everything else happens on the day.

---

## Questions

**omaib-ukomain-group@sheffield.ac.uk**

*OMAIB — Open Multimodal AI Benchmarks*
