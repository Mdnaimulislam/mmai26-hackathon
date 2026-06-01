# SONAIR Robotics Strand — Demo Scaffold

**This folder is an illustrative scaffold only. It is not a submittable template.**

Teams participating in the SONAIR robotics strand should build their own sub-portal and their own teleoperation analysis. Nothing in `demo/` is meant to be copied wholesale into a submission.

## What is included

### Example sub-portal (`sub-portals/example-uni/`)

The example sub-portal shows the **minimal shape** a valid sub-portal needs:

- Reads `theme.config.json` from the repository [`reference/`](../reference/) folder (not from `demo/`)
- Renders node name and city from that theme config
- Includes a placeholder data dashboard section

To view locally: cd to the repo root, run `python -m http.server`, then open http://localhost:8000/demo/sub-portals/example-uni/

### Exploration notebook (`notebooks/01_data_explore.ipynb`)

The notebook uses a small **synthetic** teleoperation dataset to demonstrate the “first 30 minutes” exploration flow described in the strand guide. The **real** teleoperation data will be released on the day of the hackathon.

### Demo data (`data/`)

See [`data/README.md`](data/README.md) for details on the synthetic sample CSV used by the notebook.

## What is unchanged

The JSON submission templates in [`reference/`](../reference/) remain **unchanged and blank** — teams fill them in for their own institution and federation metadata.

Do not treat files under `demo/` as submission artifacts; use `reference/` and your team’s own analysis outputs as specified in the strand guide.
