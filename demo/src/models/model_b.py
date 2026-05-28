"""Model B: random forest baseline."""

from sklearn.ensemble import RandomForestClassifier


def build_model_b():
    return RandomForestClassifier(
        n_estimators=150,
        max_depth=6,
        random_state=42,
        class_weight="balanced_subsample",
    )
