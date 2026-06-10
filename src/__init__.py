"""SCA-dream-soultion — Housing Strand trust & triage toolkit.

A small, auditable package that turns the provided housing sensor dataset into
an *honest* cold-home upgrade triage tool plus the evidence behind every verdict.

Design principle: this is a TRUST problem, not an accuracy problem. The job of
this code is not to win an AUROC leaderboard — it is to be clear about which
properties the data can and cannot support a confident decision for.
"""

from .data_pipeline import (
    FEATURES,
    FEATURES_A,
    FEATURES_B,
    load_and_merge,
    engineer_features,
    build_feature_frame,
    make_property_split,
    make_row_split,
    property_dropout_table,
)

__all__ = [
    "FEATURES",
    "FEATURES_A",
    "FEATURES_B",
    "load_and_merge",
    "engineer_features",
    "build_feature_frame",
    "make_property_split",
    "make_row_split",
    "property_dropout_table",
]
