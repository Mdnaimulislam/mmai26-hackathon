# Deploying the website online (free)

The website (`app.py`) is a Streamlit app. It is **self-healing**: on a fresh
deploy it rebuilds the model and evidence from the committed dataset
(`data/raw/housing_properties_daily.csv`), so you do **not** need to commit any
model files. First load takes ~30–60 s while it builds; after that it is instant.

> **Safe to publish:** the dataset is fully fictional — `ZZ`-prefix postcodes and
> invented street names that cannot resolve to any real UK address (see
> `data/README.md`). Nothing personal or real is exposed.

You can't deploy from the hackathon's `omaib/mmai26-hackathon` remote — host it
from **your own** GitHub repo. Two free options, easiest first.

---

## Option A — Streamlit Community Cloud (recommended)

Gives a public URL like `https://your-app-name.streamlit.app`.

1. **Make your own GitHub repo** (free): github.com → New repository → e.g.
   `cold-home-triage` → **Public** → Create.

2. **Push this code to it** (run from this folder, `mmai26-hackathon/`):
   ```bash
   git remote add myrepo https://github.com/<YOUR-USERNAME>/cold-home-triage.git
   git push myrepo SCA-dream-soultion:main
   ```
   (pushes your branch to the new repo's `main`).

3. **Deploy:** go to https://share.streamlit.io → **Sign in with GitHub** →
   **Create app** / **New app** →
   - Repository: `<YOUR-USERNAME>/cold-home-triage`
   - Branch: `main`
   - Main file path: `app.py`
   - Click **Deploy**.

4. Wait ~2–3 min (it installs `requirements.txt`, then the app builds the model on
   first load). You'll get a shareable public link. Done.

*Free tier note:* the app sleeps after inactivity and wakes on the next visit.

---

## Option B — Hugging Face Spaces (free alternative)

Gives a URL like `https://huggingface.co/spaces/<you>/cold-home-triage`.

1. huggingface.co → **New Space** → SDK: **Streamlit** → Public → Create.
2. Push this repo's files to the Space's git repo (it shows the remote URL), e.g.:
   ```bash
   git remote add hf https://huggingface.co/spaces/<YOUR-USERNAME>/cold-home-triage
   git push hf SCA-dream-soultion:main
   ```
   Ensure `app.py`, `requirements.txt`, `src/`, and `data/raw/…csv` are included
   (they are — only git-ignored model/splits are skipped, and the app rebuilds them).
3. The Space builds automatically and serves the app.

---

## Option C — run it on any machine (no hosting account)

```bash
pip install -r requirements.txt
streamlit run app.py
```
Open the printed **Local URL** (http://localhost:8501). To let others on your
network in, share the **Network URL** Streamlit prints.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| "Could not load app data" | Ensure `data/raw/housing_properties_daily.csv` is in the repo (it is committed). |
| App is slow on first open | Normal — it builds the model once, then caches. |
| `git push` rejected | The target repo must be **yours** and you must be logged in (use a GitHub Personal Access Token if prompted for a password). |
| Predictor shows a warning | The model is rebuilding; reload after the first build finishes. |
