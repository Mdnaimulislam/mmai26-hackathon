# Data — SONAIR UR5e Telemetry Dataset

The dataset is released as a ZIP file at the start of the hackathon.
Extract the contents into this `data/` directory.

---

## Dataset files

| File | Format | Rows | Key fields |
|---|---|---|---|
| `network_samples.csv` | CSV | ~9,000 | `ts`, `rtt_ms`, `jitter_ms`, `lost`, `vcap`, `cmd_type` |
| `command_ack_samples.json` | JSON | ~240 records | `ts`, `cmd_type`, `ack_latency_ms` |
| `session_audit.csv` | CSV | ~180 events | `ts`, `kind`, `detail` |

All timestamps use ISO 8601 UTC format. Parse with `parse_dates=['ts']` (CSV) or `pd.to_datetime(..., utc=True)` (JSON).

---

## What the data represents

All three files are from a single 15-minute UCL–Nottingham UR5e teleoperation session:

- **UCL** operated the robot remotely over the network
- **Nottingham** hosted the physical UR5e robot

| File | What it captures |
|---|---|
| `network_samples.csv` | Round-trip network latency between UCL and Nottingham, sampled throughout the session. `vcap` shows how the controller scaled robot speed in response to latency. |
| `command_ack_samples.json` | Individual robot commands (move, jog, estop, speed) and how long each took to be acknowledged. High `ack_latency_ms` for estop commands is a safety signal. |
| `session_audit.csv` | Session-level events: when control was granted, released, emergency stopped, or a TCP move completed. Use to annotate the RTT time-series plot. |

---

## Minimal pipeline (Data Engineer starting point)

```python
import pandas as pd
import json

# Network samples
net = pd.read_csv('data/network_samples.csv', parse_dates=['ts'])
net = net[net['rtt_ms'].notna()]
print(net['rtt_ms'].describe())

# Command acknowledgements
cmds = pd.DataFrame(json.load(open('data/command_ack_samples.json')))
cmds['ts'] = pd.to_datetime(cmds['ts'], utc=True)
print(cmds.groupby('cmd_type')['ack_latency_ms'].max())

# Session audit
audit = pd.read_csv('data/session_audit.csv', parse_dates=['ts'])
print(audit['kind'].value_counts())
```

---

Dataset released for hackathon use under terms agreed between UCL and the University of Nottingham.
**Do not redistribute outside the event.**
