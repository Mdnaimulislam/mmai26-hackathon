# Clinical Strand — Can You Trust an AI in the ICU?

**MultimodalAI'26 Hackathon · 10 June 2026**

**Challenge:** Build AI models to predict which ICU patients will deteriorate
within 24 hours, then produce the clinical evidence to decide which models
should be trusted — and under what conditions.

> Read **[STRAND_GUIDE.md](STRAND_GUIDE.md)** first if you are new to clinical AI evaluation, ICU data, or multi-person hackathon workflows.

---

## Quick start

```bash
pip install -r requirements.txt
python -c "import pandas as pd; df = pd.read_csv('data/raw/icu_patients.csv'); print(df.shape, round(df['deteriorated_24h'].mean(), 3))"
# expect: (5000, 182)  0.420
```

---

