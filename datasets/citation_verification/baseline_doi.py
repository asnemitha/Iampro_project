import csv
import requests
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

DATASET_FILE = (
    BASE_DIR / "citation_test_dataset.csv"
)

RESULTS_FILE = (
    BASE_DIR / "baseline_results.csv"
)


# ============================================================
# SETTINGS
# ============================================================

# First test with 10.
# After confirming it works, change to None.

MAX_ROWS = None


# ============================================================
# CROSSREF
# ============================================================

CROSSREF_URL = (
    "https://api.crossref.org/works"
)

TIMEOUT = 15


# ============================================================
# DOI EXTRACTION
# ============================================================

def extract_doi(text):

    import re

    pattern = (
        r"10\.\d{4,9}/"
        r"[-._;()/:A-Za-z0-9]+"
    )

    match = re.search(
        pattern,
        text or ""
    )

    if not match:
        return None

    return match.group().rstrip(
        ".,;:)]}"
    )


# ============================================================
# DOI VERIFICATION
# ============================================================

def doi_exists(doi):

    if not doi:
        return False

    url = (
        f"{CROSSREF_URL}/{doi}"
    )

    try:

        response = requests.get(
            url,
            timeout=TIMEOUT
        )

        return (
            response.status_code
            == 200
        )

    except Exception:

        return False


# ============================================================
# LOAD DATASET
# ============================================================

def load_dataset():

    if not DATASET_FILE.exists():

        raise FileNotFoundError(
            f"Dataset not found:\n"
            f"{DATASET_FILE}"
        )

    with open(
        DATASET_FILE,
        "r",
        encoding="utf-8",
        newline=""
    ) as file:

        reader = csv.DictReader(
            file
        )

        rows = list(reader)

    if MAX_ROWS is not None:

        rows = rows[:MAX_ROWS]

    return rows


# ============================================================
# METRICS
# ============================================================

def calculate_metrics(
    y_true,
    y_pred
):

    tp = 0
    tn = 0
    fp = 0
    fn = 0

    for actual, predicted in zip(
        y_true,
        y_pred
    ):

        if actual == 1 and predicted == 1:
            tp += 1

        elif actual == 0 and predicted == 0:
            tn += 1

        elif actual == 0 and predicted == 1:
            fp += 1

        elif actual == 1 and predicted == 0:
            fn += 1

    total = (
        tp + tn + fp + fn
    )

    accuracy = (
        (tp + tn) / total
        if total
        else 0
    )

    precision = (
        tp / (tp + fp)
        if (tp + fp)
        else 0
    )

    recall = (
        tp / (tp + fn)
        if (tp + fn)
        else 0
    )

    f1 = (
        2 * precision * recall
        / (precision + recall)
        if (precision + recall)
        else 0
    )

    return {
        "TP": tp,
        "TN": tn,
        "FP": fp,
        "FN": fn,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1
    }


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 70)
    print(
        "DOI-ONLY BASELINE EVALUATION"
    )
    print("=" * 70)

    rows = load_dataset()

    print()
    print(
        f"Testing {len(rows)} citations..."
    )

    y_true = []
    y_pred = []

    output_rows = []

    for index, row in enumerate(
        rows,
        start=1
    ):

        citation = row[
            "citation"
        ]

        ground_truth = int(
            row[
                "ground_truth"
            ]
        )

        doi = extract_doi(
            citation
        )

        exists = doi_exists(
            doi
        )

        # DOI-only baseline:
        #
        # DOI exists     -> VALID (0)
        # DOI not found  -> HALLUCINATED (1)

        prediction = (
            0
            if exists
            else 1
        )

        y_true.append(
            ground_truth
        )

        y_pred.append(
            prediction
        )

        output_rows.append(
            {
                "id":
                    row["id"],

                "error_type":
                    row["error_type"],

                "ground_truth":
                    ground_truth,

                "prediction":
                    prediction,

                "correct":
                    int(
                        ground_truth
                        == prediction
                    ),

                "doi":
                    doi,

                "doi_exists":
                    exists
            }
        )

        print(
            f"{index}/{len(rows)} "
            f"Prediction={prediction} "
            f"GroundTruth={ground_truth}"
        )

    # ========================================================
    # METRICS
    # ========================================================

    metrics = calculate_metrics(
        y_true,
        y_pred
    )

    # ========================================================
    # SAVE RESULTS
    # ========================================================

    with open(
        RESULTS_FILE,
        "w",
        encoding="utf-8",
        newline=""
    ) as file:

        fieldnames = [
            "id",
            "error_type",
            "ground_truth",
            "prediction",
            "correct",
            "doi",
            "doi_exists"
        ]

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()

        writer.writerows(
            output_rows
        )

    # ========================================================
    # PRINT RESULTS
    # ========================================================

    print()
    print("=" * 70)
    print(
        "DOI-ONLY BASELINE RESULTS"
    )
    print("=" * 70)

    print(
        f"Total : {len(rows)}"
    )

    print(
        f"TP    : {metrics['TP']}"
    )

    print(
        f"TN    : {metrics['TN']}"
    )

    print(
        f"FP    : {metrics['FP']}"
    )

    print(
        f"FN    : {metrics['FN']}"
    )

    print()

    print(
        f"Accuracy  : "
        f"{metrics['accuracy']:.4f}"
    )

    print(
        f"Precision : "
        f"{metrics['precision']:.4f}"
    )

    print(
        f"Recall    : "
        f"{metrics['recall']:.4f}"
    )

    print(
        f"F1 Score  : "
        f"{metrics['f1']:.4f}"
    )

    print()

    print(
        "Results saved to:"
    )

    print(
        RESULTS_FILE
    )

    print("=" * 70)


if __name__ == "__main__":
    main()