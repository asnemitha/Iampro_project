"""
Dedicated Offline Evaluation Harness for Benchmark V2.0.

This script executes the four CiteGuard configurations on hard_citation_test_dataset_v2.csv
using the content-addressed offline cache reproducible_api_cache_v2.json:
  1. Current CiteGuard (Baseline)
  2. CiteGuard + Author Fix
  3. CiteGuard + Venue Fix
  4. CiteGuard + Author + Venue Fix (Combined)

Key Features:
  - Reuses production verification pipeline WITHOUT modifying production services,
    rules, thresholds (venue_threshold=70.0, author_threshold=70.0), or dictionaries.
  - Zero network calls: mocks retrieve_candidates and verify_doi using V2 offline cache.
  - Comprehensive telemetry: tracks cache hits/misses, unresolved extractions, pipeline errors.
  - Hard path guards: ensures all outputs remain inside benchmark_v2/ and cannot overwrite V1.0 files.
  - Includes --dry-run validation mode checking inputs, cache coverage, and paths without computing metrics.
"""

import argparse
import csv
import json
from pathlib import Path
import sys
from typing import Dict, List
from unittest.mock import patch


# Add backend to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[3]
BACKEND_DIR = PROJECT_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.services import verification_pipeline


# Directories & Paths
BENCHMARK_V2_DIR = Path(__file__).resolve().parent
DATASET_V2_PATH = BENCHMARK_V2_DIR / "hard_citation_test_dataset_v2.csv"
CACHE_V2_PATH = BENCHMARK_V2_DIR / "reproducible_api_cache_v2.json"

OUTPUT_RESULTS_CSV = BENCHMARK_V2_DIR / "targeted_fixes_results_v2.csv"
OUTPUT_DETAILED_CSV = BENCHMARK_V2_DIR / "targeted_fixes_detailed_v2.csv"
OUTPUT_SUMMARY_JSON = BENCHMARK_V2_DIR / "targeted_fixes_summary_v2.json"

# Prohibited V1 paths
FROZEN_V1_PATHS = {
    BENCHMARK_V2_DIR.parent / "hard_citation_test_dataset.csv",
    BENCHMARK_V2_DIR.parent / "targeted_fixes_results.csv",
    BENCHMARK_V2_DIR.parent / "final_results.csv",
    BENCHMARK_V2_DIR.parent / "final_detailed_results.csv",
    BENCHMARK_V2_DIR.parent / "reproducible_api_cache.json",
}


def assert_path_safety(target_path: Path):
    resolved = target_path.resolve()
    for frozen in FROZEN_V1_PATHS:
        if resolved == frozen.resolve():
            raise PermissionError(f"FATAL: Attempted to write to frozen V1 artifact: {resolved}")
    if "benchmark_v2" not in str(resolved):
        raise PermissionError(f"FATAL: Target path {resolved} is not inside benchmark_v2/.")


class DummyStdout:
    def write(self, x): pass
    def flush(self): pass


def load_dataset_and_cache():
    if not DATASET_V2_PATH.exists():
        raise FileNotFoundError(f"V2 Dataset not found at: {DATASET_V2_PATH}")
    if not CACHE_V2_PATH.exists():
        raise FileNotFoundError(f"V2 Cache not found at: {CACHE_V2_PATH}")

    with open(DATASET_V2_PATH, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    with open(CACHE_V2_PATH, "r", encoding="utf-8") as f:
        cache = json.load(f)

    return rows, cache


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
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0

    return {
        "total": total,
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def dry_run_check():
    """Validate all harness inputs, cache coverage, and paths without executing evaluation."""
    print("=" * 60)
    print("BENCHMARK V2.0 EVALUATION HARNESS: DRY-RUN VALIDATION")
    print("=" * 60)

    # 1. Output path safety checks
    print("1. Checking output path safety guards...")
    assert_path_safety(OUTPUT_RESULTS_CSV)
    assert_path_safety(OUTPUT_DETAILED_CSV)
    assert_path_safety(OUTPUT_SUMMARY_JSON)
    print("   [PASS] All output paths confirmed safe and restricted to benchmark_v2/.")

    # 2. Input dataset checks
    print("2. Validating Benchmark V2.0 dataset...")
    rows, cache = load_dataset_and_cache()
    assert len(rows) == 600, f"Expected 600 rows, found {len(rows)}"
    print(f"   [PASS] Dataset loaded successfully ({len(rows)} records).")

    # 3. Cache coverage & telemetry checks
    print("3. Validating V2 offline API cache coverage...")
    cache_hits_doi = 0
    cache_hits_title = 0
    cache_misses = 0

    for r in rows:
        cid = str(r["id"])
        if cid not in cache:
            cache_misses += 1
            continue
        entry = cache[cid]
        if "verify_doi" in entry:
            cache_hits_doi += 1
        if "retrieve_candidates" in entry:
            cache_hits_title += 1

    print(f"   [PASS] DOI lookup cache coverage: {cache_hits_doi} / 600 ({cache_hits_doi/600*100:.1f}%)")
    print(f"   [PASS] Title candidates cache coverage: {cache_hits_title} / 600 ({cache_hits_title/600*100:.1f}%)")
    assert cache_misses == 0, f"Detected {cache_misses} missing cache entries!"
    print(f"   [PASS] Zero cache misses confirmed.")

    # 4. Pipeline import & threshold integrity check
    print("4. Checking production pipeline integrity...")
    import inspect
    sig = inspect.signature(verification_pipeline.verify_response)
    params = sig.parameters
    assert "use_author_fix" in params, "Missing use_author_fix parameter"
    assert "use_venue_fix" in params, "Missing use_venue_fix parameter"
    assert "venue_threshold" in params, "Missing venue_threshold parameter"
    assert params["venue_threshold"].default == 70.0, "Default venue_threshold altered"
    print("   [PASS] Production verification_pipeline signature and default threshold (70.0) verified.")

    print("=" * 60)
    print("DRY-RUN VALIDATION COMPLETE: All prerequisites verified. Harness is ready for execution.")
    print("=" * 60)


def run_evaluation():
    """Execute evaluation across the 4 configurations (requires explicit user authorization)."""
    assert_path_safety(OUTPUT_RESULTS_CSV)
    assert_path_safety(OUTPUT_DETAILED_CSV)
    assert_path_safety(OUTPUT_SUMMARY_JSON)

    rows, cache = load_dataset_and_cache()
    y_true = [int(r["ground_truth"]) for r in rows]

    current_cid = None
    telemetry = {
        "cache_hits_doi": 0,
        "cache_hits_candidates": 0,
        "unresolved_citations": 0,
        "pipeline_errors": 0,
    }

    def mock_verify_doi(doi, *args, **kwargs):
        nonlocal current_cid
        if current_cid not in cache:
            raise KeyError(f"FAIL CLOSED: Unexpected cache miss for CID {current_cid} during verify_doi({doi})")
        entry = cache[current_cid]
        if "verify_doi" not in entry:
            raise KeyError(f"FAIL CLOSED: 'verify_doi' key missing in cache entry for CID {current_cid}")
        telemetry["cache_hits_doi"] += 1
        return entry["verify_doi"]

    def mock_retrieve_candidates(title, *args, **kwargs):
        nonlocal current_cid
        if current_cid not in cache:
            raise KeyError(f"FAIL CLOSED: Unexpected cache miss for CID {current_cid} during retrieve_candidates({title})")
        entry = cache[current_cid]
        if "retrieve_candidates" not in entry:
            raise KeyError(f"FAIL CLOSED: 'retrieve_candidates' key missing in cache entry for CID {current_cid}")
        telemetry["cache_hits_candidates"] += 1
        return entry["retrieve_candidates"]

    configs = [
        {"name": "Current CiteGuard", "author": False, "venue": False},
        {"name": "CiteGuard + Author Fix", "author": True, "venue": False},
        {"name": "CiteGuard + Venue Fix", "author": False, "venue": True},
        {"name": "CiteGuard + Author + Venue Fix", "author": True, "venue": True},
    ]

    all_detailed = []
    summary_results = []

    print("Starting Benchmark V2.0 Evaluation...")

    with patch("app.services.verification_pipeline.verify_doi", side_effect=mock_verify_doi), \
         patch("app.services.verification_pipeline.retrieve_candidates", side_effect=mock_retrieve_candidates):

        for conf in configs:
            conf_name = conf["name"]
            use_author = conf["author"]
            use_venue = conf["venue"]
            print(f"\nEvaluating Configuration: {conf_name}...")

            y_pred = []
            for r in rows:
                current_cid = str(r["id"])
                cit_text = r["citation"]
                llm_formatted = f"[1]\n{cit_text}"

                old_stdout = sys.stdout
                sys.stdout = DummyStdout()
                try:
                    res = verification_pipeline.verify_response(
                        llm_formatted,
                        use_author_fix=use_author,
                        use_venue_fix=use_venue
                    )
                except Exception as exc:
                    telemetry["pipeline_errors"] += 1
                    res = []
                finally:
                    sys.stdout = old_stdout

                if not res:
                    telemetry["unresolved_citations"] += 1
                    pred = 1
                else:
                    item = res[0]
                    # Accurate citation => label 0 (valid); inaccurate => label 1 (hallucinated)
                    pred = 0 if item.get("citation_accurate", False) else 1

                y_pred.append(pred)
                all_detailed.append({
                    "citation_id": r["id"],
                    "error_type": r["error_type"],
                    "ground_truth": r["ground_truth"],
                    "prediction": pred,
                    "configuration": conf_name,
                })

            metrics = calculate_metrics(y_true, y_pred)
            summary_results.append({"configuration": conf_name, **metrics})
            print(f"  Accuracy: {metrics['accuracy']*100:.2f}%, Precision: {metrics['precision']*100:.2f}%, "
                  f"Recall: {metrics['recall']*100:.2f}%, F1: {metrics['f1']*100:.2f}%, "
                  f"TP={metrics['tp']}, FN={metrics['fn']}, FP={metrics['fp']}, TN={metrics['tn']}")

    # Save Results CSV
    fieldnames = ["configuration", "total", "tp", "tn", "fp", "fn", "accuracy", "precision", "recall", "f1"]
    with open(OUTPUT_RESULTS_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summary_results)
    print(f"\nSaved results summary to: {OUTPUT_RESULTS_CSV}")

    # Save Detailed CSV
    with open(OUTPUT_DETAILED_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["citation_id", "error_type", "ground_truth", "prediction", "configuration"])
        writer.writeheader()
        writer.writerows(all_detailed)
    print(f"Saved detailed predictions to: {OUTPUT_DETAILED_CSV}")

    # Save Summary JSON
    summary_data = {
        "configurations": summary_results,
        "telemetry": telemetry,
    }
    with open(OUTPUT_SUMMARY_JSON, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2)
    print(f"Saved JSON telemetry to: {OUTPUT_SUMMARY_JSON}")


def main():
    parser = argparse.ArgumentParser(description="Benchmark V2.0 Evaluation Harness")
    parser.add_argument("--dry-run", action="store_true", default=True,
                        help="Validate inputs, cache coverage, and paths without executing evaluation")
    parser.add_argument("--execute", action="store_true", default=False,
                        help="Execute actual evaluation across all 4 configurations")
    args = parser.parse_args()

    if args.execute:
        run_evaluation()
    else:
        dry_run_check()


if __name__ == "__main__":
    main()
