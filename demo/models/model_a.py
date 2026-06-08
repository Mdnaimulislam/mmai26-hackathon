"""Model A — PyKale Multimodal Fusion (tabular + text + vitals series).

Three-modality fusion using PyKale 0.2.0:
    • Tabular branch  : surgical context + ICU severity (FCNet encoder)
    • Text branch     : TF-IDF on free-text clinical notes (FCNet encoder)
    • Time series branch: slope / variability features from hourly vitals (FCNet encoder)
    • Fusion          : Concat → final classification head

All branches are encoded to a shared embedding dimension, concatenated,
then passed through a final MLP to produce class probabilities.

Known limitation: clinical notes are MNAR — absent for ~30 % of patients,
concentrated in the highest-ASA emergency cardiac / vascular cases.
When notes are missing, the text branch receives a zero vector, causing
the model to systematically under-estimate risk for this subgroup.
The multimodal benefit is real for fully-observed patients (AUROC ≥ 0.88)
but degrades for the notes-absent cohort.

References:
    PyKale: https://github.com/pykale/pykale  (version 0.2.0)
    Fusion: kale.embed.multimodal_fusion.Concat
    Encoder: kale.embed.nn.FCNet
"""

from __future__ import annotations

import io
import numpy as np
import pandas as pd
import torch
import torch.nn as nn

from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler

from kale.embed.nn import FCNet
from kale.embed.multimodal_fusion import Concat

TARGET = "major_complication_30d"

# ── Feature groups ────────────────────────────────────────────────────────────

TABULAR_FEATURES = [
    "surgery_enc",
    "urgency_enc",
    "asa_class",
    "op_duration_h",
    "blood_loss_imputed",
    "blood_loss_missing",
    "transfused",
    "has_diabetes",
    "has_hypertension",
    "preop_creatinine",
    "sofa_score",
    "has_notes",  # modality availability flag
]

FEATURES = TABULAR_FEATURES  # alias for consistency across strands

# Time series features extracted from vitals_series.csv (18 total)
# slope_* : linear trend over 24 h (positive = worsening for lactate/hr, etc.)
# std_*   : intra-patient variability
# late_early_* : mean(h18-24) - mean(h0-6) as a direction-of-change indicator
TS_VITALS = ["hr", "rr", "spo2", "sbp", "temp", "lactate"]
TS_FEATURES = (
    [f"slope_{v}" for v in TS_VITALS]
    + [f"std_{v}" for v in TS_VITALS]
    + [f"late_early_{v}" for v in TS_VITALS]
)

TFIDF_MAX_FEATURES = 200
EMB_DIM = 24  # shared embedding size for each modality branch
DROPOUT = 0.30


# ── Time series feature extractor ─────────────────────────────────────────────


def extract_ts_features(vitals_df: pd.DataFrame, patient_ids: list[str]) -> np.ndarray:
    """
    Compute 18 temporal features per patient from vitals_series.csv.

    Parameters
    ----------
    vitals_df   : long-format DataFrame (patient_id, hour, hr, rr, spo2, sbp, temp, lactate)
    patient_ids : ordered list of patient IDs matching the tabular DataFrame

    Returns
    -------
    np.ndarray of shape (n_patients, 18)
    """
    rows = []
    grp = vitals_df.groupby("patient_id")

    for pid in patient_ids:
        if pid not in grp.groups:
            rows.append(np.zeros(len(TS_FEATURES)))
            continue

        pv = grp.get_group(pid).sort_values("hour")
        hours = pv["hour"].values.astype(float)
        feats = []

        for v in TS_VITALS:
            vals = pv[v].values.astype(float)

            # linear slope via least-squares
            if len(hours) > 1:
                slope = np.polyfit(hours, vals, 1)[0]
            else:
                slope = 0.0

            std = float(np.std(vals))

            early = vals[hours <= 6]
            late = vals[hours >= 18]
            late_early = (
                (float(late.mean()) - float(early.mean()))
                if (len(early) > 0 and len(late) > 0)
                else 0.0
            )

            feats.extend([slope, std, late_early])

        rows.append(feats)

    return np.array(rows, dtype=np.float32)


# ── PyKale fusion network ─────────────────────────────────────────────────────


class _FusionNet(nn.Module):
    def __init__(self, n_tab: int, n_tfidf: int, n_ts: int, emb: int, dropout: float):
        super().__init__()
        self.tab_enc = FCNet([n_tab, emb * 2, emb], activation="ReLU", dropout=dropout)
        self.text_enc = FCNet(
            [n_tfidf, emb * 2, emb], activation="ReLU", dropout=dropout
        )
        self.ts_enc = FCNet([n_ts, emb * 2, emb], activation="ReLU", dropout=dropout)
        self.concat = Concat()
        self.head = nn.Sequential(
            nn.Linear(emb * 3, emb),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(emb, 2),
        )

    def forward(
        self,
        x_tab: torch.Tensor,
        x_text: torch.Tensor,
        x_ts: torch.Tensor,
    ) -> torch.Tensor:
        e_tab = self.tab_enc(x_tab)
        e_text = self.text_enc(x_text)
        e_ts = self.ts_enc(x_ts)
        fused = self.concat([e_tab, e_text, e_ts])
        return self.head(fused)


# ── Sklearn-compatible wrapper ────────────────────────────────────────────────


class ModelA(BaseEstimator, ClassifierMixin):
    """
    PyKale 3-modality fusion: tabular + TF-IDF text + ICU vitals series.

    Additional parameters vs. standard sklearn estimators:
        notes_df   : pd.DataFrame with columns [patient_id, note_text]
        vitals_df  : pd.DataFrame (long format) from vitals_series.csv

    Pass these as keyword arguments to fit() and predict_proba_full().
    """

    def __init__(
        self,
        emb_dim: int = EMB_DIM,
        dropout: float = DROPOUT,
        tfidf_max: int = TFIDF_MAX_FEATURES,
        lr: float = 5e-4,
        epochs: int = 100,
        batch_size: int = 64,
        random_state: int = 42,
    ):
        self.emb_dim = emb_dim
        self.dropout = dropout
        self.tfidf_max = tfidf_max
        self.lr = lr
        self.epochs = epochs
        self.batch_size = batch_size
        self.random_state = random_state

        self._tab_scaler = StandardScaler()
        self._ts_scaler = StandardScaler()
        self._tfidf = TfidfVectorizer(
            max_features=tfidf_max,
            sublinear_tf=True,
            ngram_range=(1, 2),
        )
        self._net = None
        self.classes_ = np.array([0, 1])

    # ── helpers ───────────────────────────────────────────────────────────────

    def _prepare(
        self,
        X: pd.DataFrame,
        notes_df: pd.DataFrame | None,
        vitals_df: pd.DataFrame | None,
        fit_mode: bool,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        pids = (
            list(X["patient_id"])
            if "patient_id" in X.columns
            else list(X.index.astype(str))
        )

        # Tabular branch
        Xtab = X[TABULAR_FEATURES].values.astype(np.float32)
        if fit_mode:
            Xtab = self._tab_scaler.fit_transform(Xtab)
        else:
            Xtab = self._tab_scaler.transform(Xtab)

        # Text branch (TF-IDF, zero vector when no note)
        pid_to_note: dict[str, str] = {}
        if notes_df is not None and len(notes_df) > 0:
            pid_to_note = dict(zip(notes_df["patient_id"], notes_df["note_text"]))
        texts = [pid_to_note.get(pid, "") for pid in pids]

        if fit_mode:
            tfidf_mat = self._tfidf.fit_transform(texts).toarray().astype(np.float32)
        else:
            tfidf_mat = self._tfidf.transform(texts).toarray().astype(np.float32)

        # Time series branch
        if vitals_df is not None and len(vitals_df) > 0:
            Xts = extract_ts_features(vitals_df, pids)
        else:
            Xts = np.zeros((len(pids), len(TS_FEATURES)), dtype=np.float32)

        if fit_mode:
            Xts = self._ts_scaler.fit_transform(Xts)
        else:
            Xts = self._ts_scaler.transform(Xts)

        return (
            torch.from_numpy(Xtab),
            torch.from_numpy(tfidf_mat),
            torch.from_numpy(Xts.astype(np.float32)),
        )

    # ── fit ───────────────────────────────────────────────────────────────────

    def fit(
        self,
        X: pd.DataFrame,
        y,
        notes_df: pd.DataFrame | None = None,
        vitals_df: pd.DataFrame | None = None,
    ) -> "ModelA":
        torch.manual_seed(self.random_state)
        np.random.seed(self.random_state)

        Xtab, Xtext, Xts = self._prepare(X, notes_df, vitals_df, fit_mode=True)
        yn = torch.from_numpy(np.array(y, dtype=np.int64))

        self._n_tab = Xtab.shape[1]
        self._n_tfidf = Xtext.shape[1]
        self._n_ts = Xts.shape[1]

        self._net = _FusionNet(
            self._n_tab, self._n_tfidf, self._n_ts, self.emb_dim, self.dropout
        )
        opt = torch.optim.Adam(self._net.parameters(), lr=self.lr, weight_decay=1e-4)
        loss_fn = nn.CrossEntropyLoss()

        n = len(yn)
        self._net.train()
        for _ in range(self.epochs):
            perm = torch.randperm(n)
            for start in range(0, n, self.batch_size):
                idx = perm[start : start + self.batch_size]
                opt.zero_grad()
                logits = self._net(Xtab[idx], Xtext[idx], Xts[idx])
                loss_fn(logits, yn[idx]).backward()
                opt.step()

        self._net.eval()
        self.classes_ = np.array([0, 1])
        return self

    # ── predict_proba (tabular-only fallback) ─────────────────────────────────

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Tabular-only inference (no text or time-series). Use predict_proba_full for full power."""
        return self.predict_proba_full(X, notes_df=None, vitals_df=None)

    def predict_proba_full(
        self,
        X: pd.DataFrame,
        notes_df: pd.DataFrame | None,
        vitals_df: pd.DataFrame | None,
    ) -> np.ndarray:
        """Full multimodal inference."""
        Xtab, Xtext, Xts = self._prepare(X, notes_df, vitals_df, fit_mode=False)
        with torch.no_grad():
            logits = self._net(Xtab, Xtext, Xts)
            probs = torch.softmax(logits, dim=1).numpy()
        return probs

    def predict(self, X: pd.DataFrame, threshold: float = 0.5) -> np.ndarray:
        return (self.predict_proba(X)[:, 1] >= threshold).astype(int)

    def feature_importance(self) -> pd.Series:
        """Approximate tabular importance from the first FCNet layer weight magnitudes."""
        if self._net is None:
            raise RuntimeError("Call fit() first.")
        try:
            w_g = self._net.tab_enc.main[1].weight_g.detach()
            w_v = self._net.tab_enc.main[1].weight_v.detach()
            w = (w_g * w_v / w_v.norm(dim=1, keepdim=True)).abs().mean(dim=0).numpy()
        except AttributeError:
            w = self._net.tab_enc.main[1].weight.detach().abs().mean(dim=0).numpy()
        return pd.Series(
            w[: len(TABULAR_FEATURES)], index=TABULAR_FEATURES
        ).sort_values(ascending=False)

    # ── serialisation (joblib) ────────────────────────────────────────────────

    def __getstate__(self):
        state = self.__dict__.copy()
        if self._net is not None:
            buf = io.BytesIO()
            torch.save(
                {
                    "state_dict": self._net.state_dict(),
                    "n_tab": self._n_tab,
                    "n_tfidf": self._n_tfidf,
                    "n_ts": self._n_ts,
                },
                buf,
            )
            state["_net_bytes"] = buf.getvalue()
        state.pop("_net", None)
        return state

    def __setstate__(self, state):
        net_bytes = state.pop("_net_bytes", None)
        self.__dict__.update(state)
        if net_bytes is not None:
            ckpt = torch.load(io.BytesIO(net_bytes), weights_only=True)
            self._net = _FusionNet(
                ckpt["n_tab"],
                ckpt["n_tfidf"],
                ckpt["n_ts"],
                self.emb_dim,
                self.dropout,
            )
            self._net.load_state_dict(ckpt["state_dict"])
            self._net.eval()
        else:
            self._net = None


def build_model_a() -> ModelA:
    return ModelA()
