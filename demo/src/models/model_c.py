"""Model C: gradient boosting baseline."""

from sklearn.ensemble import GradientBoostingClassifier


def build_model_c():
    return GradientBoostingClassifier(
        n_estimators=120,
        learning_rate=0.05,
        max_depth=3,
        random_state=42,
    )
