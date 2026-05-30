# MultimodalAI'26 Hackathon — Robotics Strand Guide — SONAIR

## The Challenge: "Can Your Robotics Evidence Be Trusted Beyond the Lab?"

---

## 1. The Scenario

SONAIR is a proposed benchmark for the robotics simulation-to-real (sim2real) gap. Instead of each university keeping its robotics work hidden inside its own lab, SONAIR allows each institution to create a public-facing sub-portal that can be discovered, embedded, and compared through a shared national portal.

In this hackathon, your team will create a creative campus sub-portal for your university or lab. The portal should show who you are, what robotics capability you have, what kind of collaborations you are interested in, and how your work could contribute to a wider UK robotics evidence network.

The challenge is not only to build a sub-portal. You will also be given a non-sensitive dataset from the UCL–Nottingham UR robot teleoperation work. UCL remotely operates the system, while the physical UR robot is located at Nottingham. Your task is to use this data to create plots, explore timing or latency issues, and propose a metric that could help describe and quantify the simulation-to-real gap.

You are allowed to use generative AI throughout the hackathon. However, you must be able to explain how you used it, why you made certain design or analysis choices, and what decisions were made by your team rather than simply copied from an AI tool.

---

## 2. Your Role In This Hackathon

Each team builds one Campus Sub-Portal and federates it with the SONAIR main portal. The main portal (the 3D UK map, the Co-Creation Space, the application server) is provided. You do not modify it. Your job is to build the content layer: a publicly accessible website that represents your lab, a `federation.json` that connects it to the national system, and an evidence dashboard built from the SONAIR dataset.

### What You Build

**A creative campus sub-portal**
A public website that represents your institution, lab identity, robotics capability, datasets, equipment, and collaboration interests.

**A SONAIR federation file**
A valid `federation.json` file that allows your sub-portal to be discovered by the SONAIR main portal.

**A robotics evidence dashboard**
A page or section that uses the Nottingham/UCL UR robot teleoperation dataset to produce useful plots and interpretation.

**A short final presentation**
A clear explanation of what you built, what the data showed, what metric you proposed, and how you used generative AI.

The aim is not to create the most complex website. The aim is to create a clear, creative, useful demonstration of how robotics evidence could be published through a federated SONAIR node.

### What You Do Not Build

- The main SONAIR portal (provided)
- The SONAIR map or Co-Creation Space (provided)
- Any private-space or API key infrastructure

---

## 3. Understanding the Task — The SONAIR Federation

Before writing any code, understand how the system works. The main portal is live; your sub-portal plugs into it through a standard protocol.

### (a) What the SONAIR portal currently shows

The main portal reads `federation-registry.json` at startup to discover registered sub-portals. The University of Nottingham's UR5e sub-portal is the founding node and reference. Your sub-portal adds to it; it does not replace it.

### (b) What a sub-portal adds

When your `federation.json` is valid and registered, the main portal automatically:
- highlights your UK administrative region on the 3D map
- creates your Co-Creation Space card
- links both to your `node.url`

This happens on every page refresh with no manual configuration.

---

## 4. The Five Deliverables

### A. Campus Sub-Portal

A publicly accessible website at a stable HTTPS URL. Must contain:
- institution name and city
- lab or group identity
- at least one equipment item or dataset description with specific details
- a collaboration section with a contact email

Must load without login in an incognito browser. Must not set `X-Frame-Options` headers.

**Failure:** 404, login required, or placeholder text only.

### B. Federation Manifest (`federation.json`)

All 10 fields are required. See Section 13A for the full field reference and Section 13B for the example. Replace every value — the template defaults must not appear in your submission.

### C. Theme Configuration (`theme.config.json`)

Named `theme.config.json` at the repository root. Must contain `institution_name`, `node_name`, `city`, `primary_color`, and `logo_url`. Your sub-portal must read this file using `fetch()` and apply `primary_color` as a CSS variable. Judges will change `primary_color` live during the demo and verify the portal updates within one minute.

**Failure:** file absent or portal ignores it.

### D. Iframe Compatibility

Your sub-portal must load cleanly inside an `<iframe>`. Use `iframe-test.html` from this repository (update `src` to your URL). Open DevTools Console: no `X-Frame-Options` or `Content-Security-Policy frame-ancestors` errors. Plain `github.io` URLs do not set these headers by default.

**Failure:** console error or blank frame.

### E. Robot Data Dashboard

You will be given a non-sensitive dataset from the UCL–Nottingham UR robot teleoperation work. Your dashboard should use this data to create plots and insights. Possible analysis includes:
- plotting robot or command data over time
- comparing UCL-side remote operation data with Nottingham-side robot data
- identifying timing offsets between data streams
- estimating latency between command and response
- showing missing data, jitter, delay, or synchronisation problems
- proposing a metric that could describe the simulation-to-real gap

---

## 5. The Federation Manifest — A Governance Decision

The `co_creation_card.description` (1–2 sentences) is the governance decision: what does your lab choose to make publicly visible? Equipment model numbers are non-sensitive; calibration parameters may not be. Dataset sizes are public; ongoing grant details may not be. Your team makes this call and explains it in the demo.

All 10 node fields are required. A missing field rejects the node entirely. Invalid manifests show as visible warnings in the Connected Sub-Portals panel during the demo.

The evidence dashboard adds a second governance layer: what you choose to highlight in the data, and what you choose not to explain, is equally a statement about what your lab considers trustworthy public evidence.

---

## 6. The Three Track Roles / Division of Work

Roles are designed for parallel work. Critical dependency: the Connector must have a live URL before the Builder can test the iframe.

### The Builder

Builds the Campus Sub-Portal frontend. Responsible for the public-facing design, content sections, and deployment.

**First 30 minutes:** Study the Nottingham reference. Write content outline (identity, equipment, datasets, collaboration). Begin `index.html` with theme `fetch()`.

### The Connector

Writes and validates `federation.json` and `theme.config.json`. Responsible for iframe compatibility and verifying the portal renders correctly inside SONAIR.

**First 30 minutes:** Fork repo, enable GitHub Pages, clone locally, create `sub-portals/YOUR-UNI/` directory, confirm live URL in incognito. This is the critical path — Builder and Data Engineer are blocked until this is done.

### The Data Engineer

Builds the robot data dashboard.

**First 30 minutes:** Download dataset. Parse timestamps to UTC. Compute mean RTT, P95 RTT, packet loss. Build RTT time-series plot and command latency histogram. Export charts as browser-displayable SVG/PNG or inline Chart.js. Hand off to Builder. Verify dashboard renders at public URL.

---

## 7. Key Concepts

| Term | Plain-English definition | In this SONAIR context |
|---|---|---|
| Federation | Independent websites sharing a common standard so they discover each other automatically. | SONAIR reads `federation-registry.json` at startup and renders every valid manifest on the UK map. |
| Sub-Portal | A self-contained website meeting the federation standard, embeddable in the main portal. | Your deliverable: a public website at your own URL that must load cleanly in an iframe. |
| `federation.json` | A JSON file at the repo root declaring who you are and where your portal is. | `validateFederationManifest()` checks all 10 fields. One invalid field = node rejected. |
| `federation-registry.json` | The organiser-controlled list of all participant manifest URLs. | Organiser adds your URL here; refresh the main portal to onboard your node. |
| Iframe | An HTML element that displays one website inside another. | Do not set `X-Frame-Options: DENY` or your portal will not embed. |
| `theme.config.json` | One file controlling your portal's colours, logo, and name without touching code. | Changing `primary_color` updates the portal within one minute after redeploy. |
| Co-Creation Space | The project board on the main portal showing all connected universities. | Auto-generated from `co_creation_card` in your `federation.json`. |
| Map pin / region | The glowing highlight on the UK map for each connected university. | `node.lat` and `node.lon` place your pin; `node.color` sets its colour. |
| Trust mechanism | The process by which the main portal decides whether to show your sub-portal. | A valid `federation.json` is the trust act; invalid manifests show as visible warnings. |
| RTT (Round-Trip Time) | Time in milliseconds for a network packet to travel to its destination and back. | Stored in `rtt_ms` in `network_samples.csv`. Use as the y-axis of the time-series plot. |
| ACK Latency | Time between sending a robot command and receiving confirmation it was accepted. | Stored in `ack_latency_ms` in `command_ack_samples.json`. High estop ACK latency is a safety concern. |
| Timestamp synchronisation | Aligning time-series data from multiple sources onto a shared timeline. | Parse `ts` fields to UTC datetime before joining dataset files for plotting. |
| Sim-to-real gap | The difference in behaviour between a simulated and a real physical robot. | The dataset captures the real-robot side of this gap. Your dashboard makes it visible. |

---

## 8. The Submission Checklist and Demo

The submission is a 2.5-minute live demo covering the federation layer and the evidence dashboard, followed by a 2.5-minute presentation.

### Pre-Submission Checklist

All five items must pass before the demo session begins. Connector owns items 2–4; Builder owns item 1; Data Engineer owns item 5.

- [ ] Sub-portal is live and publicly accessible (no login required)
- [ ] `federation.json` present at repo root and valid against the required format
- [ ] `theme.config.json` updates the portal colour when changed
- [ ] Portal embeds cleanly in `iframe-test.html` with no console errors
- [ ] Evidence dashboard is embedded in the sub-portal with both charts generated from the dataset and a written interpretation on the page

Run `python validate_submission.py` to check items 2 and 3 automatically.

### Final Presentation (2.5 minutes)

Cover all six points:

1. **What you built** — Show the live sub-portal and explain the concept behind it.
2. **Why it is designed this way** — Explain your creative choices, layout, branding, and intended audience.
3. **How it connects to SONAIR** — Show the `federation.json` file and explain how your node could be discovered by the main SONAIR portal.
4. **What the robot data shows** — Present your plots and explain what you found in the UR robot teleoperation dataset.
5. **Your proposed metric** — Explain your latency, synchronisation, or sim-to-real metric and why it matters.
6. **How you used GenAI** — Explain where GenAI helped, where it failed, and what human judgement your team added.

The strongest presentations will not simply show that something works. They will explain why the team made specific choices and how their portal could help publish trustworthy robotics evidence.

### Stretch Goals (if time permits)

- Annotate the RTT plot with GRANT/RELEASE/ESTOP events from `session_audit.csv`
- JSON schema validator or GitHub Action for `federation.json`
- Accessibility improvements: semantic headings, alt text, strong colour contrast

---

## 9. Judging Criteria

| Category | Weighting | What judges are looking for |
|---|---|---|
| Sub-portal creativity and clarity | 25% | A clear, engaging, visually considered portal that represents a lab or institution well. It should feel purposeful, not like a generic template. |
| SONAIR federation readiness | 15% | A working deployed portal, valid `federation.json`, and basic compatibility with the SONAIR federation concept. |
| Data analysis and plots | 25% | Meaningful plots from the UR robot teleoperation dataset, with sensible handling of timestamps, latency, delay, or synchronisation. |
| Proposed metric | 15% | A clear and defensible metric that could help describe latency, synchronisation, sim-to-real transfer, or remote-to-real behaviour. |
| Final presentation and GenAI use | 20% | Clear explanation of the portal, data findings, metric, design choices, and limitations. Thoughtful use of GenAI, with explanation of what it helped with and what decisions were made by the team. |

### What does a strong submission look like?

| Criterion | Weak | Strong |
|---|---|---|
| Sub-portal content | Template placeholder text only. No equipment list, no contact email. | Real institution name, specific equipment (model numbers), dataset details, and a contact email. |
| `federation.json` | All 10 fields present but lat/lon still at template defaults. Wrong map region. | All 10 fields with real values. Correct coordinates. Meaningful `co_creation_card.description`. |
| Theme config | `theme.config.json` present but portal ignores it. `primary_color` hard-coded in HTML. | `fetch()` reads `theme.config.json` on load. Colour change propagates in under 60 seconds. |
| Evidence dashboard | Dashboard section absent or charts are screenshots. Interpretation missing. | RTT plot and latency histogram generated from the provided CSV/JSON. Interpretation cites real numbers and addresses operator safety. |
| Demo and governance | Fewer than 3 steps completed. Cannot explain governance choice or data findings. | All five steps in 2.5 minutes. Governance and data interpretation both explained with specific numbers. |

---

## 10. Your First 30 Minutes

The Connector's first 30 minutes are the critical path — all other roles are blocked on the live URL until it exists.

| Role | First 30-minute tasks | Why this order |
|---|---|---|
| Connector | Fork repo, enable GitHub Pages, clone locally, create `sub-portals/YOUR-UNI/` directory, start with a minimal `index.html`, confirm live URL in incognito. | Builder cannot test iframe until URL is public. All other work depends on this. |
| Builder | Study Nottingham reference. Write content outline (identity, equipment, datasets, collaboration). Begin `index.html` with theme `fetch()`. | Content takes the most time. Starting from an outline ensures substantive output. |
| Data Engineer | Download dataset. Parse `ts` to UTC datetime. Compute mean RTT, P95, packet loss. Produce first RTT plot draft. | A working plot in the first 30 minutes confirms the data pipeline works and leaves time to refine. |

---

## 11. SONAIR Reference

Keep this section open during the build. Field names and validation rules match `validateFederationManifest()` exactly.

### 13A. `federation.json` — Complete Field Reference

All 10 fields are required. A single missing or out-of-range value causes the node to be skipped with a warning.

| Field | Type | Description | Example / Rule |
|---|---|---|---|
| `node.id` | String | Unique lowercase identifier, no spaces. | `"your-uni-id"` e.g. `"edinburgh"` |
| `node.name` | String | Full official institution name. | `"Your University Full Name"` |
| `node.city` | String | City where the lab is located. | `"Your City"` |
| `node.lat` | Number | Latitude. UK range: 49–61. Do not use template default. | Replace `53.3814` with your real latitude |
| `node.lon` | Number | Longitude. UK range: -8 to 2. Do not use template default. | Replace `-1.4884` with your real longitude |
| `node.color` | String | Hex colour for the map pin. | `"#72F5B8"` (use your brand colour) |
| `node.url` | String | Full HTTPS URL of your sub-portal. Must be publicly reachable. | `"https://your-uni.github.io/sonair-portal"` |
| `co_creation_card.title` | String | Short project title on the Co-Creation card. | `"Your Lab Project Title"` |
| `co_creation_card.tags` | Array | 2–5 keyword strings. Must be a JSON array. | `["Robotics", "YourTag"]` |
| `co_creation_card.description` | String | 1–2 sentences: your equipment or datasets. This is your governance statement. | Write your own — do not copy the template default. |

### 13B. `federation.json` Example

Replace **every** value. The defaults shown (Sheffield, 53.3814, -1.4884) must **not** appear in your submission.

```json
{
  "node": {
    "id": "your-uni-id",
    "name": "Your University Full Name",
    "city": "Your City",
    "lat": 99.9999,
    "lon": -9.9999,
    "color": "#YOUR_BRAND_HEX",
    "url": "https://your-uni.github.io/sonair-portal"
  },
  "co_creation_card": {
    "title": "Your Lab Project Title",
    "tags": ["YourTag1", "Robotics"],
    "description": "Describe your real equipment and collaboration needs."
  }
}
```

### 13C. Iframe Compatibility Test

Open `iframe-test.html` from this repository, change `src` to your URL, open in a browser. Open DevTools (F12) → Console. No `X-Frame-Options` or `Content-Security-Policy frame-ancestors` errors should appear. Plain `github.io` URLs do not set these headers by default.

### 13D. `theme.config.json` — Field Reference

| Field | Type | Description | Example |
|---|---|---|---|
| `institution_name` | String | Full institution name. Page title and hero heading. | `"Your University Full Name"` |
| `node_name` | String | Short display name for the node. | `"Your Lab Node Name"` |
| `city` | String | City name. | `"Your City"` |
| `primary_color` | String (hex) | Main brand colour. Judges will change this live during the demo. | `"#72F5B8"` |
| `logo_url` | String (URL) | Path or URL to your institution logo. | `"./assets/logo.png"` |

### 13E. Adding Your Node to the Registry

Once `federation.json` is live, give the organiser your manifest URL. They add it to `federation-registry.json`. Refreshing the main portal then automatically connects your node, highlights your map region, and adds your Co-Creation card.

### 13F. SONAIR UR5e Telemetry Dataset — File Reference

The dataset ZIP is provided at the start of the hackathon. All files are from a 15-minute UCL–Nottingham UR5e teleoperation session. All timestamps use ISO 8601 UTC format.

| File | Format | Key fields | Use in dashboard |
|---|---|---|---|
| `network_samples.csv` | CSV, ~9,000 rows | `ts`, `rtt_ms`, `jitter_ms`, `lost`, `vcap`, `cmd_type` | RTT time-series plot. `vcap` shows latency-adaptive speed scaling. |
| `command_ack_samples.json` | JSON, ~240 records | `ts`, `cmd_type` (movel/jog_joint/estop/set_speed), `ack_latency_ms` | Command latency histogram. Group by `cmd_type`; highlight estop. |
| `session_audit.csv` | CSV, ~180 events | `ts`, `kind` (GRANT/RELEASE/ESTOP/TCP_MOVE), `detail` | Annotate RTT plot with event markers. |

**Minimal Python pipeline:**

```python
import pandas as pd, json

net = pd.read_csv('data/network_samples.csv', parse_dates=['ts'])
net = net[net['rtt_ms'].notna()]

cmds = pd.DataFrame(json.load(open('data/command_ack_samples.json')))
cmds['ts'] = pd.to_datetime(cmds['ts'], utc=True)

# RTT summary
print(net['rtt_ms'].describe())

# Max ACK latency per command type
print(cmds.groupby('cmd_type')['ack_latency_ms'].max())
```

Dataset released for hackathon use under terms agreed between UCL and the University of Nottingham. Do not redistribute outside the event.
