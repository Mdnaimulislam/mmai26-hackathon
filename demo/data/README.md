# Demo data (synthetic)

The file `raw/network_samples.csv` is **synthetic**. It uses a reduced number of rows and fewer columns than the real teleoperation dataset that will be released on hackathon day.

It exists only so the demo notebook (`../notebooks/01_data_explore.ipynb`) can run locally during setup — not as a stand-in for production or competition data.

## Columns

| Column         | Description                                      |
|----------------|--------------------------------------------------|
| `timestamp`    | Sample time (ISO-style or epoch-style string)    |
| `rtt_ms`       | Round-trip time in milliseconds                  |
| `jitter_ms`    | Jitter in milliseconds                           |
| `packet_loss`  | Packet loss proportion or rate for the sample    |
