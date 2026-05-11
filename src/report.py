"""Report generation for the Clinical Strand.

What participants touch
-----------------------
METRIC_REGISTRY  — add entries here for any custom metrics you computed.
                   Each entry tells the report what the metric means and
                   what it means in the ICU context specifically.

What is provided
----------------
generate_html_report()  — renders any metrics dict dynamically.
generate_omaib_card()   — produces an OMAIB-compatible JSON model card.
generate_full_submission() — bundles model cards into a submission object.

No metric name is hardcoded in the HTML output. Every key in your metrics
dict will appear in the report. Known keys get full clinical descriptions;
unknown keys appear with their raw name and a 'custom metric' label.
"""
from __future__ import annotations

from datetime import date
from dataclasses import dataclass, field


# ══════════════════════════════════════════════════════════════════════════════
# METRIC REGISTRY  — extend this with your own metrics
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class MetricInfo:
    label:              str          # short display name
    full_name:          str          # expanded name
    general:            str          # what it measures in general ML terms
    strand:             str          # what it means in THIS ICU context
    value_range:        str = ""     # e.g. "0 to 1 (higher is better)"
    deployment_guide:   str = ""     # threshold guidance for clinicians


METRIC_REGISTRY: dict[str, MetricInfo] = {

    "auroc": MetricInfo(
        label="AUROC",
        full_name="Area Under the Receiver Operating Characteristic Curve",
        general=(
            "Measures overall discrimination: the probability that the model "
            "assigns a higher score to a randomly chosen positive case than to "
            "a randomly chosen negative case. Threshold-independent."
        ),
        strand=(
            "If you pick one ICU patient who will deteriorate and one who will "
            "not, AUROC is the probability the model ranks the deteriorating "
            "patient higher. 0.5 = random chance; 1.0 = perfect discrimination."
        ),
        value_range="0 to 1 (higher is better; 0.5 = random)",
        deployment_guide=(
            "For ICU decision support: >= 0.85 is clinically viable. "
            "< 0.70 is close to random for this dataset and warrants NOT APPROVED."
        ),
    ),

    "auprc": MetricInfo(
        label="AUPRC",
        full_name="Area Under the Precision-Recall Curve",
        general=(
            "Summarises the trade-off between alert accuracy (precision/PPV) "
            "and the fraction of sick patients caught (recall/sensitivity) "
            "across all possible thresholds."
        ),
        strand=(
            "More informative than AUROC when the class is imbalanced. "
            "In this dataset ~34% of patients deteriorate. A baseline that "
            "flags every patient scores AUPRC = 0.34; any useful model must "
            "exceed this substantially."
        ),
        value_range="0 to 1 (higher is better; baseline ≈ prevalence rate)",
        deployment_guide=">= 0.65 is considered useful for ward triage support.",
    ),

    "brier_score": MetricInfo(
        label="Brier Score",
        full_name="Brier Score (Mean Squared Probability Error)",
        general=(
            "Measures calibration accuracy: the mean squared difference between "
            "predicted probabilities and actual outcomes. A perfectly calibrated "
            "model with probability p is right p fraction of the time."
        ),
        strand=(
            "Determines whether the model's risk scores can be used directly "
            "to prioritise care. A Brier score near 0 means predicted "
            "probabilities are trustworthy. A score above 0.25 means the "
            "scores are unreliable for thresholding — treat them as ranks only."
        ),
        value_range="0 (perfect) to 1 (worst); lower is always better",
        deployment_guide=(
            "< 0.10 excellent; < 0.15 good; < 0.25 moderate — use as ranks only; "
            "> 0.25 poor — do not use raw scores in clinical workflows."
        ),
    ),

    "sensitivity": MetricInfo(
        label="Sensitivity",
        full_name="Sensitivity / Recall / True Positive Rate",
        general=(
            "The fraction of all actual positive cases that the model correctly "
            "flags at the chosen threshold."
        ),
        strand=(
            "Of every 100 ICU patients who will deteriorate in the next 24 hours, "
            "Sensitivity is how many the model flags for clinical attention. "
            "The patients it misses are false negatives — the most dangerous error "
            "type in this context, as a missed deterioration can lead to preventable death."
        ),
        value_range="0 to 1 (higher is better)",
        deployment_guide=(
            ">= 0.80 is typically required for life-critical decision support. "
            "< 0.70 means the model misses more than 30 in 100 deteriorating patients."
        ),
    ),

    "specificity": MetricInfo(
        label="Specificity",
        full_name="Specificity / True Negative Rate",
        general=(
            "The fraction of all actual negative cases correctly identified by "
            "the model — patients correctly given the all-clear."
        ),
        strand=(
            "Of every 100 ICU patients who will NOT deteriorate, Specificity is "
            "how many the model correctly reassures. Low specificity means excessive "
            "false alarms: clinical staff are asked to escalate patients who were "
            "never at risk, wasting resource and eroding trust in the system."
        ),
        value_range="0 to 1 (higher is better)",
        deployment_guide=(
            ">= 0.75 is generally needed to avoid alert fatigue. "
            "< 0.60 means more than 40% of stable patients trigger unnecessary alerts."
        ),
    ),

    "ppv": MetricInfo(
        label="PPV",
        full_name="Positive Predictive Value (Precision)",
        general=(
            "Of all cases the model flags as positive, the fraction that are "
            "truly positive. The 'precision' of an alert."
        ),
        strand=(
            "When the model raises a high-risk alert, PPV is how often it is right. "
            "A PPV of 0.70 means 3 in 10 alerts are false alarms. "
            "Clinical staff must decide: act on every alert (lower PPV tolerable) "
            "or only high-confidence ones (higher PPV needed, more misses)."
        ),
        value_range="0 to 1 (higher is better)",
        deployment_guide=(
            ">= 0.65 is workable if alert review is lightweight. "
            "< 0.50 means the majority of alerts are false — likely to cause alert fatigue."
        ),
    ),

    "npv": MetricInfo(
        label="NPV",
        full_name="Negative Predictive Value",
        general=(
            "Of all cases the model gives the all-clear for, the fraction that "
            "truly do not deteriorate. The 'safety' of a negative prediction."
        ),
        strand=(
            "When the model says a patient is low-risk, NPV is how safe that "
            "reassurance is. A NPV of 0.90 means 10 in 100 cleared patients "
            "will still deteriorate. Whether this is acceptable depends on whether "
            "cleared patients receive any residual monitoring protocol."
        ),
        value_range="0 to 1 (higher is better)",
        deployment_guide=(
            ">= 0.90 is typically required before a model can reduce monitoring intensity. "
            ">= 0.95 before using the model to actively deprioritise patients."
        ),
    ),

    "f1": MetricInfo(
        label="F1 Score",
        full_name="F1 Score (Harmonic Mean of PPV and Sensitivity)",
        general=(
            "A single summary of the precision–recall trade-off. "
            "Useful when you care equally about missing positives and raising false alarms."
        ),
        strand=(
            "Balances missed deteriorations against false alarms. "
            "In ICU settings, missed deteriorations are usually more costly than "
            "false alarms — so F1 may under-value improvements in sensitivity. "
            "Always interpret F1 alongside sensitivity individually."
        ),
        value_range="0 to 1 (higher is better)",
        deployment_guide=">= 0.70 is reasonable; always check sensitivity alongside.",
    ),

}

# ── To add a custom metric, append an entry here: ────────────────────────────
# METRIC_REGISTRY["my_metric"] = MetricInfo(
#     label="My Metric",
#     full_name="Full Name of My Metric",
#     general="What this metric measures in general.",
#     strand="What this metric means specifically for ICU deterioration prediction.",
#     value_range="0 to 1 (higher is better)",
#     deployment_guide="When is this metric good enough?",
# )


# ══════════════════════════════════════════════════════════════════════════════
# SKIP THESE KEYS WHEN RENDERING THE METRICS TABLE
# ══════════════════════════════════════════════════════════════════════════════
_META_KEYS = {"model", "threshold", "tp", "fp", "tn", "fn", "n_positive", "n_total"}

# Keys shown in the HTML summary table (order matters)
_SUMMARY_KEYS = ["auroc", "auprc", "sensitivity", "specificity", "brier_score"]


# ══════════════════════════════════════════════════════════════════════════════
# OMAIB CARD
# ══════════════════════════════════════════════════════════════════════════════

def generate_omaib_card(
    model_name: str,
    metrics: dict,
    verdict: str,
    conditions: str,
    narrative: str,
    subgroup_gaps: dict | None = None,
) -> dict:
    """Return an OMAIB-compatible model card dict (schema: omaib-clinical-v0.3).

    All keys in `metrics` are included — no filtering.
    """
    return {
        "schema_version": "omaib-clinical-v0.3",
        "submission_type": "model_safety_report",
        "strand": "clinical",
        "hackathon": "MultimodalAI26",
        "evaluation_date": str(date.today()),
        "model": {
            "name":        model_name,
            "verdict":     verdict,
            "conditions":  conditions,
            "narrative":   narrative,
            "metrics":     {k: v for k, v in metrics.items() if k not in _META_KEYS},
            "subgroup_gaps": subgroup_gaps or {},
        },
    }


def generate_full_submission(
    team_name: str,
    team_members: str,
    model_cards: list[dict],
    overall_notes: str,
) -> dict:
    return {
        "schema_version":  "omaib-clinical-v0.3",
        "submission_type": "model_safety_report",
        "strand":          "clinical",
        "hackathon":       "MultimodalAI26",
        "submitted":       str(date.today()),
        "team":            {"name": team_name, "members": team_members},
        "models":          [c["model"] for c in model_cards],
        "overall_notes":   overall_notes,
    }


# ══════════════════════════════════════════════════════════════════════════════
# HTML REPORT  (dynamic — renders whatever keys are in the metrics dict)
# ══════════════════════════════════════════════════════════════════════════════

_VERDICT_COLOUR = {
    "APPROVE":      "#1a7a1a",
    "CONDITIONAL":  "#b35c00",
    "NOT APPROVED": "#a01010",
}

_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Model Safety Report — Clinical Strand</title>
<style>
  body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 40px auto;
          max-width: 980px; color: #1a1a1a; line-height: 1.6; }}
  h1   {{ color: #1a3a5c; border-bottom: 3px solid #1a3a5c; padding-bottom: 6px; }}
  h2   {{ color: #1a3a5c; margin-top: 36px; }}
  h3   {{ color: #2c5282; }}
  table {{ border-collapse: collapse; width: 100%; margin: 14px 0; font-size: 0.88em; }}
  th   {{ background: #1a3a5c; color: white; padding: 8px 12px; text-align: left; }}
  td   {{ border: 1px solid #ccd6e0; padding: 7px 12px; vertical-align: top; }}
  tr:nth-child(even) td {{ background: #f0f5fa; }}
  .verdict {{ display: inline-block; padding: 5px 16px; border-radius: 4px;
              font-weight: bold; font-size: 1.05em; color: white; }}
  .model-card {{ border: 1px solid #ccd6e0; border-radius: 6px;
                 padding: 20px 24px; margin: 24px 0; background: #fafcff; }}
  .meta   {{ color: #555; font-size: 0.87em; }}
  .narrative  {{ background: #f5f9ff; border-left: 4px solid #1a3a5c;
                 padding: 12px 16px; margin: 10px 0; border-radius: 0 4px 4px 0; }}
  .conditions {{ background: #fff8f0; border-left: 4px solid #b35c00;
                 padding: 10px 14px; margin: 10px 0; border-radius: 0 4px 4px 0; }}
  .failure-summary {{ background: #f4f8f4; border-left: 4px solid #2c7a2c;
                      padding: 14px 18px; margin: 16px 0; border-radius: 0 6px 6px 0; }}
  .team-response {{ background: #fffef0; border-left: 3px solid #b8860b;
                    padding: 6px 10px; margin: 0; font-style: italic; color: #333; }}
  .failure-analysis {{ background: #f8f4ff; border-left: 4px solid #6a3d9a;
                       padding: 14px 18px; margin: 16px 0; border-radius: 0 6px 6px 0; }}
  .custom-badge {{ font-size: 0.75em; background: #e8f0fe; color: #1a3a5c;
                   padding: 1px 6px; border-radius: 3px; }}
  footer {{ margin-top: 60px; font-size: 0.78em; color: #888;
            border-top: 1px solid #ddd; padding-top: 12px; }}
</style>
</head>
<body>
<h1>Model Safety Report</h1>
<p class="meta">
  <strong>Strand:</strong> Clinical &nbsp;|&nbsp;
  <strong>Hackathon:</strong> MultimodalAI&rsquo;26 &nbsp;|&nbsp;
  <strong>Team:</strong> {team_name} &nbsp;|&nbsp;
  <strong>Date:</strong> {eval_date}
</p>

<h2>Summary</h2>
<table>
<tr><th>Model</th>{summary_headers}<th>Verdict</th></tr>
{summary_rows}
</table>

{model_sections}

<h2>Team Notes</h2>
<div class="narrative">{overall_notes}</div>

<footer>
  MultimodalAI&rsquo;26 Hackathon &mdash; Clinical Strand &mdash;
  OMAIB-compatible (schema: omaib-clinical-v0.3) &mdash; {eval_date}
</footer>
</body>
</html>"""

_MODEL_SECTION = """
<div class="model-card">
<h2>{model_name}
  &nbsp;<span class="verdict" style="background:{verdict_colour}">{verdict}</span>
</h2>

<h3>Clinical deployment assessment</h3>
{failure_summary}

<h3>Performance metrics</h3>
<table>
<tr>
  <th>Metric</th><th>Full name</th><th>Value</th>
  <th>What it measures</th><th>In the ICU context</th>
</tr>
{metric_rows}
</table>

<h3>Conditions for deployment</h3>
<div class="conditions">{conditions}</div>

<h3>Assessment narrative</h3>
<div class="narrative">{narrative}</div>

{subgroup_table}
{failure_analysis}
</div>"""

_SUBGROUP_SECTION = """
<h3>Subgroup analysis</h3>
<table>
<tr><th>Group</th><th>Value</th><th>N</th>
    <th>AUROC</th><th>Sensitivity</th><th>Specificity</th><th>AUROC gap</th></tr>
{rows}
</table>"""


def _metric_row(key: str, value) -> str:
    info = METRIC_REGISTRY.get(key)
    is_custom = info is None
    label     = info.label      if info else key.upper()
    full_name = info.full_name  if info else key
    general   = info.general    if info else "Custom metric added by the team."
    strand    = info.strand     if info else "—"
    badge     = ' <span class="custom-badge">custom</span>' if is_custom else ""
    val_str   = f"{value:.4f}" if isinstance(value, float) else str(value)
    return (
        f"<tr><td><strong>{label}</strong>{badge}</td>"
        f"<td style='color:#444;font-size:0.85em'>{full_name}</td>"
        f"<td><strong>{val_str}</strong></td>"
        f"<td>{general}</td>"
        f"<td>{strand}</td></tr>"
    )


def _subgroup_rows(gaps_list: list[dict]) -> str:
    rows = []
    for g in gaps_list:
        gap = g.get("auroc_gap", "—")
        gap_str = f"{gap:+.3f}" if isinstance(gap, float) else str(gap)
        colour = " style='color:#a01010;font-weight:bold'" if isinstance(gap, float) and gap < -0.05 else ""
        rows.append(
            f"<tr><td>{g.get('group_col','')}</td><td>{g.get('group_value','')}</td>"
            f"<td>{g.get('n_group','')}</td><td>{g.get('auroc','')}</td>"
            f"<td>{g.get('sensitivity','')}</td><td>{g.get('specificity','')}</td>"
            f"<td{colour}>{gap_str}</td></tr>"
        )
    return "\n".join(rows)




def _team_cell(text: str) -> str:
    safe = (text or "").strip()
    if not safe:
        return "<td><em style='color:#aaa'>Not provided</em></td>"
    return f'<td><div class="team-response">{safe}</div></td>'


def _clinical_deployment_html(
    ward_sim: dict | None,
    q_answers: dict | None = None,
    q_narratives: dict | None = None,
) -> str:
    """Render the clinical deployment assessment section for the HTML report."""
    if not ward_sim:
        return ""
    n_sick       = ward_sim.get("n_sick", "—")
    caught       = ward_sim.get("caught", "—")
    missed       = ward_sim.get("missed", "—")
    false_alarms = ward_sim.get("false_alarms", "—")
    cleared      = ward_sim.get("cleared", "—")
    ans          = q_answers or {}
    qn           = q_narratives or {}

    def _radio_cell(val: str) -> str:
        safe = (val or "—").strip()
        return f"<td style='font-size:0.9em;color:#444'>{safe}</td>"

    rows = (
        f"<tr><td><strong>Q1.</strong> How many will the model miss?</td>"
        f"{_radio_cell(ans.get('miss_acceptable','—'))}"
        f"{_team_cell(qn.get('q1',''))}</tr>\n"
        f"<tr><td><strong>Q2.</strong> When the model alerts, is it right?</td>"
        f"{_radio_cell(ans.get('trust_alert','—'))}"
        f"{_team_cell(qn.get('q2',''))}</tr>\n"
        f"<tr><td><strong>Q3.</strong> When the model clears, is it safe?</td>"
        f"{_radio_cell(ans.get('trust_clear','—'))}"
        f"{_team_cell(qn.get('q3',''))}</tr>\n"
        f"<tr><td><strong>Q4.</strong> How well does it discriminate?</td>"
        f"<td>—</td>"
        f"{_team_cell(qn.get('q4',''))}</tr>\n"
        f"<tr><td><strong>Q5.</strong> Can risk scores set care priorities?</td>"
        f"{_radio_cell(ans.get('calib_ok','—'))}"
        f"{_team_cell(qn.get('q5',''))}</tr>"
    )
    return (
        '<div class="failure-summary">'
        f"<h4>Ward simulation (per 100 patients, approximately {n_sick} deteriorating)</h4>"
        "<table>"
        '<tr><th style="background:#1a7a1a">Caught (TP)</th>'
        '<th style="background:#a01010">Missed (FN)</th>'
        '<th style="background:#b35c00">False alarms (FP)</th>'
        "<th>Correct clears (TN)</th></tr>"
        f'<tr><td style="color:#1a7a1a;font-weight:bold;font-size:1.3em;text-align:center">{caught}</td>'
        f'<td style="color:#a01010;font-weight:bold;font-size:1.3em;text-align:center">{missed}</td>'
        f'<td style="color:#b35c00;font-weight:bold;font-size:1.3em;text-align:center">{false_alarms}</td>'
        f'<td style="font-size:1.3em;text-align:center">{cleared}</td></tr>'
        "</table>"
        "<h4>Five clinical deployment questions</h4>"
        "<table>"
        '<tr><th style="width:30%">Question</th>'
        "<th style='width:35%'>Team checklist</th>"
        "<th style='width:35%'>Team response</th></tr>"
        f"\n{rows}\n"
        "</table></div>"
    )


def _failure_analysis_html(failure_narratives: dict | None) -> str:
    fn_ = failure_narratives or {}
    questions = [
        ("Who does this model miss?",                    fn_.get("fn", "")),
        ("What do false alarms look like?",              fn_.get("fp", "")),
        ("What is the model using to make predictions?", fn_.get("features", "")),
        ("Where do the models disagree?",                fn_.get("disagree", "")),
    ]
    if not any(v.strip() for _, v in questions):
        return ""
    rows = "\n".join(
        f"<tr><td><strong>{q}</strong></td>{_team_cell(v)}</tr>"
        for q, v in questions
    )
    return (
        '<div class="failure-analysis">'
        "<h3>Failure analysis — team interpretations</h3>"
        "<table>"
        "<tr><th style='width:35%'>Question</th>"
        "<th style='width:65%'>Team interpretation</th></tr>"
        f"\n{rows}\n"
        "</table></div>"
    )


def generate_html_report(
    team_name: str,
    overall_notes: str,
    model_cards: list[dict],
    subgroup_data: dict[str, list[dict]] | None = None,
) -> str:
    """Render the Model Safety Report as HTML.

    Parameters
    ----------
    model_cards : list of dicts, each with keys:
        model_name  str
        verdict     str — APPROVE / CONDITIONAL / NOT APPROVED
        conditions  str
        narrative   str
        metrics     dict — output of compute_metrics() (any keys accepted)
        ward_sim    dict — optional, output of _ward_simulation() or clinical_translation()
        q_answers   dict — optional, team's answers to clinical deployment questions
    subgroup_data : optional, maps model_name → list of subgroup metric dicts
    """
    eval_date     = str(date.today())
    subgroup_data = subgroup_data or {}

    # Collect all metric keys across all models (for consistent column headers)
    all_metric_keys = []
    for mc in model_cards:
        for k in mc.get("metrics", {}):
            if k not in _META_KEYS and k not in all_metric_keys:
                all_metric_keys.append(k)

    # Summary table headers — show _SUMMARY_KEYS first, then extras
    ordered_summary = [k for k in _SUMMARY_KEYS if k in all_metric_keys]
    ordered_summary += [k for k in all_metric_keys if k not in _SUMMARY_KEYS]
    summary_headers = "".join(
        f"<th>{METRIC_REGISTRY[k].label if k in METRIC_REGISTRY else k.upper()}</th>"
        for k in ordered_summary
    )

    # Summary rows
    summary_rows = []
    for mc in model_cards:
        m  = mc.get("metrics", {})
        v  = mc.get("verdict", "—")
        vc = _VERDICT_COLOUR.get(v, "#555")
        cells = "".join(
            f"<td>{m.get(k, '—')}</td>" for k in ordered_summary
        )
        summary_rows.append(
            f"<tr><td>{mc['model_name']}</td>{cells}"
            f"<td><span class='verdict' style='background:{vc}'>{v}</span></td></tr>"
        )

    # Per-model sections
    sections = []
    for mc in model_cards:
        m   = mc.get("metrics", {})
        v   = mc.get("verdict", "—")
        vc  = _VERDICT_COLOUR.get(v, "#555")
        mrows = "\n".join(
            _metric_row(k, val)
            for k, val in m.items()
            if k not in _META_KEYS
        )
        gaps = subgroup_data.get(mc["model_name"], [])
        sub_html        = _SUBGROUP_SECTION.format(rows=_subgroup_rows(gaps)) if gaps else ""
        failure_html    = _clinical_deployment_html(
            mc.get("ward_sim"), mc.get("q_answers", {}), mc.get("q_narratives", {})
        )
        fa_analysis_html = _failure_analysis_html(mc.get("failure_narratives"))
        sections.append(
            _MODEL_SECTION.format(
                model_name       = mc["model_name"],
                verdict          = v,
                verdict_colour   = vc,
                metric_rows      = mrows,
                conditions       = mc.get("conditions") or "None stated.",
                narrative        = mc.get("narrative")  or "No narrative provided.",
                subgroup_table   = sub_html,
                failure_summary  = failure_html,
                failure_analysis = fa_analysis_html,
            )
        )

    return _HTML_TEMPLATE.format(
        team_name       = team_name or "—",
        eval_date       = eval_date,
        summary_headers = summary_headers,
        summary_rows    = "\n".join(summary_rows),
        model_sections  = "\n".join(sections),
        overall_notes   = overall_notes or "No overall notes provided.",
    )
