"""
run_venue_experiment.py
=======================
Executes the controlled Venue Fix experiment across all 4 CiteGuard configurations
on the frozen 600-citation dataset using reproducible_api_cache.json.

Compares experimental predictions against:
1. Saved camera-ready paper predictions (targeted_fixes_detailed.csv)
2. Previous current-code predictions (prediction_changes.csv)
"""

import sys
import json
import csv
from pathlib import Path
from unittest.mock import patch

# Setup paths
base_dir = Path(__file__).resolve().parents[3]
backend_dir = base_dir / "backend"
sys.path.insert(0, str(backend_dir))

from app.services import verification_pipeline

exp_dir = Path(__file__).resolve().parent
dataset_path = base_dir / "datasets" / "citation_verification" / "hard_citation_test_dataset.csv"
cache_path = base_dir / "datasets" / "citation_verification" / "reproducible_api_cache.json"
saved_detailed_path = base_dir / "datasets" / "citation_verification" / "targeted_fixes_detailed.csv"
diag_changes_path = base_dir / "datasets" / "citation_verification" / "diagnostics" / "prediction_changes.csv"

# Load files
with open(dataset_path, "r", encoding="utf-8") as f:
    dataset = list(csv.DictReader(f))

with open(cache_path, "r", encoding="utf-8") as f:
    cache = json.load(f)

with open(saved_detailed_path, "r", encoding="utf-8") as f:
    saved_rows = list(csv.DictReader(f))
saved_map = {(r["citation_id"], r["configuration"]): int(r["prediction"]) for r in saved_rows}

with open(diag_changes_path, "r", encoding="utf-8") as f:
    prev_rows = list(csv.DictReader(f))
prev_map = {(r["citation_id"], r["configuration"]): int(r["current_prediction"]) for r in prev_rows}

CURRENT_CID = None
def mock_verify_doi(doi, *args, **kwargs):
    return cache[CURRENT_CID]["verify_doi"]

def mock_retrieve_candidates(title, *args, **kwargs):
    return cache[CURRENT_CID]["retrieve_candidates"]

class DummyFile(object):
    def write(self, x): pass
    def flush(self): pass

def calculate_metrics(y_true, y_pred):
    tp = tn = fp = fn = 0
    for true, pred in zip(y_true, y_pred):
        if true == 1 and pred == 1:
            tp += 1
        elif true == 0 and pred == 0:
            tn += 1
        elif true == 0 and pred == 1:
            fp += 1
        elif true == 1 and pred == 0:
            fn += 1
            
    total = tp + tn + fp + fn
    accuracy = (tp + tn) / total if total > 0 else 0.0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    
    return {
        "total": total,
        "tp": tp, "tn": tn, "fp": fp, "fn": fn,
        "accuracy": accuracy, "precision": precision,
        "recall": recall, "f1": f1
    }

def main():
    print("=" * 80)
    print("  CITATON GUARD: EXPERIMENTAL VENUE FIX EVALUATION")
    print("=" * 80)

    configs = [
        ("Current CiteGuard", False, False),
        ("CiteGuard + Author Fix", True, False),
        ("CiteGuard + Venue Fix", False, True),
        ("CiteGuard + Author + Venue Fix", True, True)
    ]

    all_detailed_rows = []
    summary_results = {}

    with patch("app.services.verification_pipeline.verify_doi", side_effect=mock_verify_doi), \
         patch("app.services.verification_pipeline.retrieve_candidates", side_effect=mock_retrieve_candidates):
        
        for cfg_name, use_auth, use_ven in configs:
            print(f"\nEvaluating configuration: {cfg_name} (author_fix={use_auth}, venue_fix={use_ven})...")
            y_true = []
            y_pred = []
            cfg_rows = []

            global CURRENT_CID
            for row in dataset:
                cid = row["id"]
                CURRENT_CID = cid
                citation = row["citation"]
                gt = int(row["ground_truth"])
                cat = row["error_type"]
                llm_formatted = f"[1]\n{citation}"

                parsed = verification_pipeline.parse_citation(llm_formatted)

                sys.stdout = DummyFile()
                try:
                    results = verification_pipeline.verify_response(
                        llm_formatted,
                        use_author_fix=use_auth,
                        use_venue_fix=use_ven
                    )
                except Exception as e:
                    results = []
                sys.stdout = sys.__stdout__

                if not results:
                    pred = 1
                    matched_paper = {}
                    meta_errors = ["Pipeline exception or no candidate found"]
                    scores = {}
                else:
                    res = results[0]
                    pred = 0 if res.get("citation_accurate", False) else 1
                    matched_paper = {
                        "title": res.get("matched_title"),
                        "authors": res.get("matched_authors"),
                        "year": res.get("matched_year"),
                        "venue": res.get("matched_venue"),
                        "doi": res.get("matched_doi")
                    }
                    meta_errors = res.get("metadata_errors", []) or res.get("reason", [])
                    scores = {
                        "title_similarity": res.get("title_similarity", 0),
                        "author_similarity": res.get("author_similarity", 0),
                        "year_match": res.get("year_match", False),
                        "venue_match": res.get("venue_match", False),
                        "doi_match": res.get("doi_match", False),
                        "hallucination_score": res.get("hallucination_score", 0)
                    }

                y_true.append(gt)
                y_pred.append(pred)

                saved_pred = saved_map.get((cid, cfg_name))
                prev_pred = prev_map.get((cid, cfg_name))

                # Improvement / regression relative to previous current code
                prev_correct = (prev_pred == gt)
                exp_correct = (pred == gt)
                improved = (not prev_correct and exp_correct)
                regressed = (prev_correct and not exp_correct)

                parsed_authors = "; ".join(parsed.get("authors") or [])
                matched_authors = "; ".join(matched_paper.get("authors") or [])

                rec = {
                    "citation_id": cid,
                    "benchmark_category": cat,
                    "ground_truth": gt,
                    "configuration": cfg_name,
                    "saved_paper_pred": saved_pred,
                    "previous_current_pred": prev_pred,
                    "experimental_pred": pred,
                    "diff_from_saved": (pred != saved_pred),
                    "diff_from_previous": (pred != prev_pred),
                    "improved_over_previous": improved,
                    "regressed_from_previous": regressed,
                    "claimed_title": parsed.get("title", ""),
                    "claimed_authors": parsed_authors,
                    "claimed_year": parsed.get("year", ""),
                    "claimed_venue": parsed.get("venue", ""),
                    "claimed_doi": parsed.get("doi", ""),
                    "matched_title": matched_paper.get("title", ""),
                    "matched_authors": matched_authors,
                    "matched_year": matched_paper.get("year", ""),
                    "matched_venue": matched_paper.get("venue", ""),
                    "matched_doi": matched_paper.get("doi", ""),
                    "title_score": scores.get("title_similarity", 0),
                    "author_score": scores.get("author_similarity", 0),
                    "year_match": scores.get("year_match", False),
                    "venue_match": scores.get("venue_match", False),
                    "doi_match": scores.get("doi_match", False),
                    "decision_reason": " | ".join(meta_errors) if meta_errors else "Accurate citation"
                }
                cfg_rows.append(rec)
                all_detailed_rows.append(rec)

            m = calculate_metrics(y_true, y_pred)
            
            # Category breakdown
            cat_metrics = {}
            for cat in ["valid", "corrupted_authors", "wrong_year", "wrong_venue", "doi_mismatch", "plausible_fabricated"]:
                cat_rows = [r for r in cfg_rows if r["benchmark_category"] == cat]
                cat_true = [r["ground_truth"] for r in cat_rows]
                cat_pred = [r["experimental_pred"] for r in cat_rows]
                cat_correct = sum(1 for t, p in zip(cat_true, cat_pred) if t == p)
                cat_metrics[cat] = {
                    "correct": cat_correct,
                    "total": len(cat_rows),
                    "accuracy": cat_correct / len(cat_rows) if len(cat_rows) > 0 else 0
                }

            summary_results[cfg_name] = {
                "overall": m,
                "categories": cat_metrics,
                "improvements_over_previous": sum(1 for r in cfg_rows if r["improved_over_previous"]),
                "regressions_from_previous": sum(1 for r in cfg_rows if r["regressed_from_previous"])
            }

    # Save detailed CSV
    out_csv = exp_dir / "experimental_detailed_results.csv"
    fieldnames = list(all_detailed_rows[0].keys())
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_detailed_rows)
    print(f"\n[OK] Saved experimental detailed results to: {out_csv.name}")

    # Save summary JSON
    out_json = exp_dir / "experimental_summary.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(summary_results, f, indent=2)
    print(f"[OK] Saved experimental summary to: {out_json.name}")

    # Terminal Report
    print("\n" + "=" * 80)
    print("EXPERIMENTAL EVALUATION RESULTS SUMMARY")
    print("=" * 80)
    header = f"{'Configuration':<32} {'Accuracy':<10} {'Precision':<10} {'Recall':<10} {'F1-Score':<10} {'TP':<5} {'FP':<5} {'TN':<5} {'FN':<5}"
    print(header)
    print("-" * len(header))

    for cfg_name in [c[0] for c in configs]:
        res = summary_results[cfg_name]["overall"]
        acc = f"{res['accuracy']*100:.2f}%"
        pre = f"{res['precision']*100:.2f}%"
        rec = f"{res['recall']*100:.2f}%"
        f1  = f"{res['f1']*100:.2f}%"
        print(f"{cfg_name:<32} {acc:<10} {pre:<10} {rec:<10} {f1:<10} {res['tp']:<5} {res['fp']:<5} {res['tn']:<5} {res['fn']:<5}")

    print("\n" + "=" * 80)
    print("PER-CATEGORY ACCURACY ACROSS 6 ERROR TYPES:")
    print("=" * 80)
    categories = ["valid", "corrupted_authors", "wrong_year", "wrong_venue", "doi_mismatch", "plausible_fabricated"]
    cat_header = f"{'Configuration':<32} " + " ".join([f"{c[:10]:<10}" for c in categories])
    print(cat_header)
    print("-" * len(cat_header))
    for cfg_name in [c[0] for c in configs]:
        cats = summary_results[cfg_name]["categories"]
        row_str = " ".join([f"{cats[c]['correct']}/{cats[c]['total']:<6}" for c in categories])
        print(f"{cfg_name:<32} {row_str}")

    print("\n" + "=" * 80)
    print("DELTA VS PREVIOUS CURRENT CODE:")
    print("=" * 80)
    for cfg_name in [c[0] for c in configs]:
        imp = summary_results[cfg_name]["improvements_over_previous"]
        reg = summary_results[cfg_name]["regressions_from_previous"]
        print(f"{cfg_name:<32} Improvements = +{imp}, Regressions = -{reg}, Net Change = {imp - reg:+d}")

if __name__ == "__main__":
    main()
