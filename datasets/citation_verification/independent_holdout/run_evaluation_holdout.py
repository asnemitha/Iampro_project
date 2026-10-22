"""
Dedicated Offline Evaluation Harness for Independent Multidisciplinary Holdout Benchmark.

Executes all four CiteGuard configurations on independent_holdout_dataset.csv:
  1. Baseline (CiteGuard default)
  2. Author Fix
  3. Venue Fix
  4. Combined (Author Fix + Venue Fix)

Features:
  - Strict offline execution using reproducible_api_cache_holdout.json.
  - Zero modification to production code, similarity services, or published thresholds (venue=70.0, author=70.0).
  - Comprehensive performance metrics: TP, TN, FP, FN, Accuracy, Precision, Recall,
    Specificity, Balanced Accuracy, F1-Score, Macro-F1.
  - Exact Wilson 95% confidence intervals.
  - Disciplinary stratification: CS, Medicine, Natural Sciences, Humanities/Social Sciences.
  - Error-type stratification: corrupted_authors, wrong_venue, wrong_year, doi_mismatch, plausible_fabricated.
  - Telemetry: outputs holdout_results.csv, holdout_detailed_results.csv, holdout_summary.json.
"""

import argparse
import csv
import json
import math
from pathlib import Path
import re
import sys
from typing import Dict, List, Tuple
from unittest.mock import patch

# Add backend to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[3]
BACKEND_DIR = PROJECT_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.services import verification_pipeline

HOLDOUT_DIR = Path(__file__).resolve().parent
DATASET_CSV = HOLDOUT_DIR / "independent_holdout_dataset.csv"
CACHE_JSON = HOLDOUT_DIR / "reproducible_api_cache_holdout.json"

OUTPUT_RESULTS_CSV = HOLDOUT_DIR / "holdout_results.csv"
OUTPUT_DETAILED_CSV = HOLDOUT_DIR / "holdout_detailed_results.csv"
OUTPUT_SUMMARY_JSON = HOLDOUT_DIR / "holdout_summary.json"


class DummyStdout:
    def write(self, x): pass
    def flush(self): pass


def wilson_ci(k: int, n: int, confidence: float = 0.95) -> Tuple[float, float]:
    """Calculate Wilson score interval for binomial proportions."""
    if n == 0:
        return 0.0, 0.0
    z = 1.959963984540054  # 95% normal quantile
    p_hat = k / n
    denominator = 1 + (z ** 2) / n
    centre = (p_hat + (z ** 2) / (2 * n)) / denominator
    margin = (z / denominator) * math.sqrt((p_hat * (1 - p_hat) / n) + ((z ** 2) / (4 * (n ** 2))))
    lower = max(0.0, centre - margin)
    upper = min(1.0, centre + margin)
    return lower * 100.0, upper * 100.0


def calculate_metrics(y_true: List[int], y_pred: List[int]) -> Dict:
    tp = tn = fp = fn = 0
    for t, p in zip(y_true, y_pred):
        if t == 1 and p == 1:
            tp += 1
        elif t == 0 and p == 0:
            tn += 1
        elif t == 0 and p == 1:
            fp += 1
        elif t == 1 and p == 0:
            fn += 1

    total = tp + tn + fp + fn
    accuracy = (tp + tn) / total if total else 0.0
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    specificity = tn / (tn + fp) if (tn + fp) else 0.0
    balanced_acc = (recall + specificity) / 2.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) else 0.0

    # Class 0 F1 (Valid)
    prec_0 = tn / (tn + fn) if (tn + fn) else 0.0
    rec_0 = tn / (tn + fp) if (tn + fp) else 0.0
    f1_0 = (2 * prec_0 * rec_0) / (prec_0 + rec_0) if (prec_0 + rec_0) else 0.0

    macro_f1 = (f1 + f1_0) / 2.0

    # 95% Confidence Intervals
    acc_ci_low, acc_ci_high = wilson_ci(tp + tn, total)
    rec_ci_low, rec_ci_high = wilson_ci(tp, tp + fn)
    spec_ci_low, spec_ci_high = wilson_ci(tn, tn + fp)
    prec_ci_low, prec_ci_high = wilson_ci(tp, tp + fp)

    return {
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "total": total,
        "accuracy": round(accuracy * 100.0, 2),
        "accuracy_ci_95": [round(acc_ci_low, 2), round(acc_ci_high, 2)],
        "precision": round(precision * 100.0, 2),
        "precision_ci_95": [round(prec_ci_low, 2), round(prec_ci_high, 2)],
        "recall": round(recall * 100.0, 2),
        "recall_ci_95": [round(rec_ci_low, 2), round(rec_ci_high, 2)],
        "specificity": round(specificity * 100.0, 2),
        "specificity_ci_95": [round(spec_ci_low, 2), round(spec_ci_high, 2)],
        "balanced_accuracy": round(balanced_acc * 100.0, 2),
        "f1": round(f1 * 100.0, 2),
        "macro_f1": round(macro_f1 * 100.0, 2),
    }


def run_evaluation():
    print("=" * 80)
    print("INDEPENDENT MULTIDISCIPLINARY HOLDOUT BENCHMARK EVALUATION")
    print("=" * 80)

    with open(DATASET_CSV, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    with open(CACHE_JSON, "r", encoding="utf-8") as f:
        cache = json.load(f)

    print(f"Loaded {len(rows)} citations from: {DATASET_CSV.name}")
    print(f"Loaded {len(cache)} cached items from: {CACHE_JSON.name}")

    configs = [
        ("Baseline", False, False),
        ("Author Fix", True, False),
        ("Venue Fix", False, True),
        ("Combined", True, True),
    ]

    all_detailed_records = []
    summary_results = []
    config_summaries = {}

    for config_name, use_author_fix, use_venue_fix in configs:
        print(f"\nEvaluating Configuration: {config_name} (author_fix={use_author_fix}, venue_fix={use_venue_fix})...")
        y_true = []
        y_pred = []
        detailed_preds = []

        for row in rows:
            cid = str(row["id"])
            gt = int(row["ground_truth"])
            cit = row["citation"]
            discipline = row["discipline"]
            error_type = row["error_type"]

            cached_entry = cache.get(cid, {})

            def mock_verify_doi(doi):
                return cached_entry.get("verify_doi")

            def mock_retrieve_candidates(title, *args, **kwargs):
                return cached_entry.get("retrieve_candidates", [])

            # Suppress verbose terminal logging
            real_stdout = sys.stdout
            try:
                sys.stdout = DummyStdout()
                with patch("app.services.verification_pipeline.verify_doi", side_effect=mock_verify_doi), \
                     patch("app.services.verification_pipeline.retrieve_candidates", side_effect=mock_retrieve_candidates):

                    results = verification_pipeline.verify_response(
                        cit,
                        use_author_fix=use_author_fix,
                        use_venue_fix=use_venue_fix,
                    )
            finally:
                sys.stdout = real_stdout

            if not results:
                pred_error = 1
                hallucination_type = "Parsing / Extraction Error"
                paper_exists = False
                citation_accurate = False
                candidate_score = 0
            else:
                res = results[0]
                citation_accurate = bool(res.get("citation_accurate", False))
                paper_exists = res.get("paper_exists")
                hallucination_type = res.get("hallucination_type", "Unknown")
                candidate_score = res.get("candidate_score", 0)
                pred_error = 0 if citation_accurate else 1

            y_true.append(gt)
            y_pred.append(pred_error)

            pred_record = {
                "id": row["id"],
                "discipline": discipline,
                "error_type": error_type,
                "ground_truth": gt,
                "configuration": config_name,
                "predicted_error": pred_error,
                "citation_accurate": citation_accurate,
                "paper_exists": str(paper_exists),
                "hallucination_type": hallucination_type,
                "candidate_score": candidate_score,
                "source_doi": row.get("source_doi", ""),
                "donor_doi": row.get("donor_doi", ""),
            }
            detailed_preds.append(pred_record)
            all_detailed_records.append(pred_record)

        # Calculate overall metrics
        metrics = calculate_metrics(y_true, y_pred)
        metrics["configuration"] = config_name
        summary_results.append(metrics)

        # Calculate metrics by discipline
        discipline_metrics = {}
        for disc in ["computer_science", "medicine_biomedical", "natural_sciences", "humanities_social_sciences"]:
            disc_true = [gt for gt, p in zip(y_true, detailed_preds) if p["discipline"] == disc]
            disc_pred = [p["predicted_error"] for p in detailed_preds if p["discipline"] == disc]
            discipline_metrics[disc] = calculate_metrics(disc_true, disc_pred)

        # Calculate metrics by error type
        error_type_metrics = {}
        for err in ["valid", "corrupted_authors", "wrong_venue", "wrong_year", "doi_mismatch", "plausible_fabricated"]:
            err_true = [gt for gt, p in zip(y_true, detailed_preds) if p["error_type"] == err]
            err_pred = [p["predicted_error"] for p in detailed_preds if p["error_type"] == err]
            err_m = calculate_metrics(err_true, err_pred)
            error_type_metrics[err] = {
                "total": len(err_true),
                "correct": err_m["tp"] if err != "valid" else err_m["tn"],
                "accuracy": round(((err_m["tp"] if err != "valid" else err_m["tn"]) / len(err_true)) * 100.0, 2),
            }

        config_summaries[config_name] = {
            "overall": metrics,
            "by_discipline": discipline_metrics,
            "by_error_type": error_type_metrics,
        }

        print(f"  Accuracy: {metrics['accuracy']}% (CI: {metrics['accuracy_ci_95']}) | F1: {metrics['f1']}% | Recall: {metrics['recall']}% | Specificity: {metrics['specificity']}%")
        print(f"  Confusion Matrix: TP={metrics['tp']}, TN={metrics['tn']}, FP={metrics['fp']}, FN={metrics['fn']}")

    # Write summary CSV
    with open(OUTPUT_RESULTS_CSV, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "configuration", "tp", "tn", "fp", "fn", "total",
            "accuracy", "precision", "recall", "specificity",
            "balanced_accuracy", "f1", "macro_f1"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for s in summary_results:
            row_dict = {k: s[k] for k in fieldnames}
            writer.writerow(row_dict)

    # Write detailed CSV
    with open(OUTPUT_DETAILED_CSV, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "id", "discipline", "error_type", "ground_truth", "configuration",
            "predicted_error", "citation_accurate", "paper_exists",
            "hallucination_type", "candidate_score", "source_doi", "donor_doi"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_detailed_records)

    # Write summary JSON
    with open(OUTPUT_SUMMARY_JSON, "w", encoding="utf-8") as f:
        json.dump(config_summaries, f, indent=2)

    print(f"\n[SUCCESS] Completed Independent Holdout Benchmark Evaluation.")
    print(f"  Summary Results CSV : {OUTPUT_RESULTS_CSV}")
    print(f"  Detailed Results CSV: {OUTPUT_DETAILED_CSV}")
    print(f"  Full Summary JSON   : {OUTPUT_SUMMARY_JSON}")


if __name__ == "__main__":
    run_evaluation()
