import csv
import json
import sys
from pathlib import Path
from collections import Counter


# ============================================================
# PROJECT PATH
# ============================================================

# This file is:
# CiteGuard/datasets/citation_verification/evaluate_citeguard.py

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = PROJECT_ROOT / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


# ============================================================
# IMPORT CITEGUARD VERIFICATION PIPELINE
# ============================================================

from app.services.citation_verifier import verify_response


# ============================================================
# FILE PATHS
# ============================================================

# IMPORTANT:
# Use the NEW HARD benchmark
DATASET_FILE = (
    Path(__file__).resolve().parent
    / "hard_citation_test_dataset.csv"
)

# Separate output files so old results are not overwritten
RESULTS_FILE = (
    Path(__file__).resolve().parent
    / "hard_evaluation_results.csv"
)

SUMMARY_FILE = (
    Path(__file__).resolve().parent
    / "hard_evaluation_summary.json"
)


# ============================================================
# SETTINGS
# ============================================================

# None = evaluate complete 600-row benchmark
#
# For quick testing:
# MAX_ROWS = 10
#
# For final IEEE experiment:
MAX_ROWS = None


# ============================================================
# BINARY METRICS
# ============================================================

def calculate_metrics(y_true, y_pred):

    tp = 0
    tn = 0
    fp = 0
    fn = 0

    for actual, predicted in zip(y_true, y_pred):

        if actual == 1 and predicted == 1:
            tp += 1

        elif actual == 0 and predicted == 0:
            tn += 1

        elif actual == 0 and predicted == 1:
            fp += 1

        elif actual == 1 and predicted == 0:
            fn += 1

    total = tp + tn + fp + fn

    accuracy = (
        (tp + tn) / total
        if total
        else 0.0
    )

    precision = (
        tp / (tp + fp)
        if (tp + fp)
        else 0.0
    )

    recall = (
        tp / (tp + fn)
        if (tp + fn)
        else 0.0
    )

    f1 = (
        2 * precision * recall
        / (precision + recall)
        if (precision + recall)
        else 0.0
    )

    return {
        "true_positive": tp,
        "true_negative": tn,
        "false_positive": fp,
        "false_negative": fn,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


# ============================================================
# READ HARD BENCHMARK
# ============================================================

def load_dataset():

    if not DATASET_FILE.exists():

        raise FileNotFoundError(
            f"\nHard benchmark not found:\n"
            f"{DATASET_FILE}\n\n"
            f"Make sure hard_citation_test_dataset.csv exists "
            f"inside datasets/citation_verification/"
        )

    with open(
        DATASET_FILE,
        "r",
        encoding="utf-8",
        newline=""
    ) as file:

        reader = csv.DictReader(file)
        rows = list(reader)

    if not rows:

        raise RuntimeError(
            "The hard benchmark dataset is empty."
        )

    # --------------------------------------------------------
    # HARD BENCHMARK SCHEMA
    # --------------------------------------------------------
    #
    # id
    # citation
    # ground_truth
    # error_type
    # source_doi
    # description
    #

    required_columns = {
        "id",
        "citation",
        "ground_truth",
        "error_type",
    }

    actual_columns = set(rows[0].keys())

    missing = required_columns - actual_columns

    if missing:

        raise RuntimeError(
            "Hard benchmark is missing columns: "
            + ", ".join(sorted(missing))
        )

    if MAX_ROWS is not None:
        rows = rows[:MAX_ROWS]

    return rows


# ============================================================
# EXTRACT PREDICTION
# ============================================================

def get_prediction(verification_result):

    if not verification_result:
        return 1

    # CiteGuard convention:
    #
    # exists = True
    #     -> valid citation = 0
    #
    # exists = False
    #     -> hallucinated citation = 1

    exists = verification_result.get(
        "exists",
        False
    )

    if exists:
        return 0

    return 1


# ============================================================
# RUN ONE CITATION
# ============================================================

def evaluate_row(row):

    citation = row["citation"]

    ground_truth = int(
        row["ground_truth"]
    )

    error_type = row["error_type"]

    try:

        # Run the ACTUAL CiteGuard verification pipeline
        results = verify_response(citation)

        if not results:

            prediction = 1

            result = {
                "exists": False,
                "confidence": "No verification result",
                "hallucination_score": 100,
            }

        else:

            # One citation per benchmark row
            result = results[0]

            prediction = get_prediction(result)

        return {
            "id": row["id"],
            "error_type": error_type,
            "ground_truth": ground_truth,
            "prediction": prediction,
            "correct": int(
                ground_truth == prediction
            ),

            "citation": citation,

            "source_doi": row.get(
                "source_doi",
                ""
            ),

            "description": row.get(
                "description",
                ""
            ),

            "matched_title": result.get(
                "matched_title"
            ),

            "matched_doi": result.get(
                "matched_doi"
            ),

            "title_similarity": result.get(
                "title_similarity"
            ),

            "author_similarity": result.get(
                "author_similarity"
            ),

            "year_match": result.get(
                "year_match"
            ),

            "doi_match": result.get(
                "doi_match"
            ),

            "venue_match": result.get(
                "venue_match"
            ),

            "hallucination_score": result.get(
                "hallucination_score"
            ),

            "confidence": result.get(
                "confidence"
            ),
        }

    except Exception as exc:

        print()
        print(
            f"ERROR on row {row['id']}:"
        )
        print(exc)

        # Verification failure is treated as
        # hallucinated/unverified.
        prediction = 1

        return {
            "id": row["id"],
            "error_type": error_type,
            "ground_truth": ground_truth,
            "prediction": prediction,
            "correct": int(
                ground_truth == prediction
            ),

            "citation": citation,

            "source_doi": row.get(
                "source_doi",
                ""
            ),

            "description": row.get(
                "description",
                ""
            ),

            "matched_title": None,
            "matched_doi": None,

            "title_similarity": 0,
            "author_similarity": 0,

            "year_match": False,
            "doi_match": False,
            "venue_match": False,

            "hallucination_score": 100,

            "confidence": "Verification Error",
        }


# ============================================================
# SAVE INDIVIDUAL RESULTS
# ============================================================

def save_results(results):

    fieldnames = [
        "id",
        "error_type",
        "ground_truth",
        "prediction",
        "correct",
        "citation",
        "source_doi",
        "description",
        "matched_title",
        "matched_doi",
        "title_similarity",
        "author_similarity",
        "year_match",
        "doi_match",
        "venue_match",
        "hallucination_score",
        "confidence",
    ]

    with open(
        RESULTS_FILE,
        "w",
        encoding="utf-8",
        newline=""
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()

        writer.writerows(results)


# ============================================================
# PER-ERROR-TYPE METRICS
# ============================================================

def calculate_category_metrics(results):

    categories = {}

    error_types = sorted(
        set(
            row["error_type"]
            for row in results
        )
    )

    for error_type in error_types:

        category_rows = [
            row
            for row in results
            if row["error_type"] == error_type
        ]

        y_true = [
            int(row["ground_truth"])
            for row in category_rows
        ]

        y_pred = [
            int(row["prediction"])
            for row in category_rows
        ]

        categories[error_type] = calculate_metrics(
            y_true,
            y_pred
        )

    return categories


# ============================================================
# PRINT SUMMARY
# ============================================================

def print_summary(
    overall,
    category_metrics,
    results
):

    print()
    print("=" * 80)
    print("CITEGUARD HARD BENCHMARK RESULTS")
    print("=" * 80)

    print()

    print(
        f"Total citations : {len(results)}"
    )

    print()

    print(
        f"True Positive   : "
        f"{overall['true_positive']}"
    )

    print(
        f"True Negative   : "
        f"{overall['true_negative']}"
    )

    print(
        f"False Positive  : "
        f"{overall['false_positive']}"
    )

    print(
        f"False Negative  : "
        f"{overall['false_negative']}"
    )

    print()

    print(
        f"Accuracy        : "
        f"{overall['accuracy']:.4f}"
    )

    print(
        f"Precision       : "
        f"{overall['precision']:.4f}"
    )

    print(
        f"Recall          : "
        f"{overall['recall']:.4f}"
    )

    print(
        f"F1 Score        : "
        f"{overall['f1']:.4f}"
    )

    print()

    print("=" * 80)
    print("PER-ERROR-TYPE PERFORMANCE")
    print("=" * 80)

    print()

    print(
        f"{'Category':<25}"
        f"{'Count':>8}"
        f"{'Accuracy':>12}"
        f"{'Precision':>12}"
        f"{'Recall':>12}"
        f"{'F1':>12}"
    )

    print("-" * 85)

    for category, metrics in category_metrics.items():

        count = sum(
            1
            for row in results
            if row["error_type"] == category
        )

        print(
            f"{category:<25}"
            f"{count:>8}"
            f"{metrics['accuracy']:>12.4f}"
            f"{metrics['precision']:>12.4f}"
            f"{metrics['recall']:>12.4f}"
            f"{metrics['f1']:>12.4f}"
        )

    print()


# ============================================================
# SAVE SUMMARY JSON
# ============================================================

def save_summary(
    overall,
    category_metrics,
    results
):

    summary = {

        "dataset": str(
            DATASET_FILE
        ),

        "total_samples":
            len(results),

        "overall_metrics":
            overall,

        "category_metrics":
            category_metrics,

        "prediction_distribution":
            dict(
                Counter(
                    row["prediction"]
                    for row in results
                )
            ),

        "ground_truth_distribution":
            dict(
                Counter(
                    row["ground_truth"]
                    for row in results
                )
            ),
    }

    with open(
        SUMMARY_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            summary,
            file,
            indent=4
        )


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 80)
    print("CITEGUARD HARD BENCHMARK EVALUATION")
    print("=" * 80)

    print()

    print(
        "Dataset:",
        DATASET_FILE
    )

    print()

    rows = load_dataset()

    print(
        f"Loaded {len(rows)} test cases."
    )

    print()

    print(
        "Starting CiteGuard verification..."
    )

    print(
        "The system will verify each citation "
        "using the actual CiteGuard pipeline."
    )

    print(
        "This may take some time because "
        "scholarly APIs are queried."
    )

    results = []

    for index, row in enumerate(
        rows,
        start=1
    ):

        print()
        print("=" * 80)

        print(
            f"TEST CASE "
            f"{index}/{len(rows)}"
        )

        print(
            f"ID: {row['id']}"
        )

        print(
            f"Type: "
            f"{row['error_type']}"
        )

        print(
            f"Ground truth: "
            f"{row['ground_truth']}"
        )

        result = evaluate_row(row)

        results.append(result)

        print()

        print(
            "Prediction:",
            result["prediction"]
        )

        print(
            "Correct:",
            result["correct"]
        )

    # ========================================================
    # SAVE RESULTS
    # ========================================================

    save_results(results)

    # ========================================================
    # OVERALL METRICS
    # ========================================================

    y_true = [
        int(row["ground_truth"])
        for row in results
    ]

    y_pred = [
        int(row["prediction"])
        for row in results
    ]

    overall = calculate_metrics(
        y_true,
        y_pred
    )

    # ========================================================
    # CATEGORY METRICS
    # ========================================================

    category_metrics = (
        calculate_category_metrics(
            results
        )
    )

    # ========================================================
    # SAVE SUMMARY
    # ========================================================

    save_summary(
        overall,
        category_metrics,
        results
    )

    # ========================================================
    # PRINT
    # ========================================================

    print_summary(
        overall,
        category_metrics,
        results
    )

    print(
        "=" * 80
    )

    print(
        "FILES CREATED"
    )

    print(
        f"Detailed results:"
        f"\n{RESULTS_FILE}"
    )

    print(
        f"\nSummary:"
        f"\n{SUMMARY_FILE}"
    )

    print(
        "=" * 80
    )


if __name__ == "__main__":
    main()