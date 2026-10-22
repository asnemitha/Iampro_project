import csv
import re
import requests
from pathlib import Path
from difflib import SequenceMatcher


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

DATASET_FILE = BASE_DIR / "citation_test_dataset.csv"

RESULTS_FILE = BASE_DIR / "crossref_metadata_results.csv"


# ============================================================
# SETTINGS
# ============================================================

# First test with 10.
# After confirming it works, change to None.

MAX_ROWS = None

TIMEOUT = 15

TITLE_THRESHOLD = 85.0
AUTHOR_THRESHOLD = 70.0
VENUE_THRESHOLD = 75.0


# ============================================================
# CROSSREF
# ============================================================

CROSSREF_URL = "https://api.crossref.org/works"


# ============================================================
# NORMALIZE TEXT
# ============================================================

def normalize_text(text):

    if not text:
        return ""

    text = str(text).lower()

    text = re.sub(
        r"[^a-z0-9\s]",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ============================================================
# STRING SIMILARITY
# ============================================================

def similarity(text1, text2):

    text1 = normalize_text(text1)
    text2 = normalize_text(text2)

    if not text1 or not text2:
        return 0.0

    return (
        SequenceMatcher(
            None,
            text1,
            text2
        ).ratio()
        * 100
    )


# ============================================================
# TITLE SIMILARITY
# ============================================================

def title_similarity(
    title1,
    title2
):

    if not title1 or not title2:
        return 0.0

    sequence_score = similarity(
        title1,
        title2
    )

    words1 = set(
        normalize_text(title1).split()
    )

    words2 = set(
        normalize_text(title2).split()
    )

    if not words1 or not words2:
        return sequence_score

    intersection = len(
        words1 & words2
    )

    union = len(
        words1 | words2
    )

    token_score = (
        intersection / union
    ) * 100

    return (
        sequence_score * 0.7
        + token_score * 0.3
    )


# ============================================================
# DOI EXTRACTION
# ============================================================

def extract_doi(text):

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
# DOI NORMALIZATION
# ============================================================

def normalize_doi(doi):

    if not doi:
        return ""

    doi = str(doi).strip().lower()

    doi = doi.replace(
        "https://doi.org/",
        ""
    )

    doi = doi.replace(
        "http://doi.org/",
        ""
    )

    doi = doi.replace(
        "doi:",
        ""
    )

    return doi.strip()


# ============================================================
# PARSE TITLE
# ============================================================

def parse_title(text):

    match = re.search(
        r"Title\s*:\s*[\"“](.*?)[\"”]",
        text,
        re.IGNORECASE
    )

    if match:
        return match.group(1).strip()

    match = re.search(
        r"Title\s*:\s*(.*?)(?:\n|$)",
        text,
        re.IGNORECASE
    )

    if match:

        return (
            match.group(1)
            .strip()
            .strip("\"'“”")
        )

    return ""


# ============================================================
# PARSE AUTHORS
# ============================================================

def parse_authors(text):

    match = re.search(
        r"Authors?\s*:\s*(.*?)(?:\n|$)",
        text,
        re.IGNORECASE
    )

    if not match:
        return []

    raw = match.group(1).strip()

    raw = raw.replace(
        "**",
        ""
    )

    # Dataset uses semicolon-separated
    # authors.

    parts = re.split(
        r";|\s+and\s+",
        raw
    )

    authors = []

    for part in parts:

        part = part.strip()

        if part:
            authors.append(
                part
            )

    return authors


# ============================================================
# PARSE YEAR
# ============================================================

def parse_year(text):

    match = re.search(
        r"(?:Year|Published(?:\s+in)?)\s*:\s*(\d{4})",
        text,
        re.IGNORECASE
    )

    if match:

        try:
            return int(
                match.group(1)
            )

        except ValueError:
            pass

    return None


# ============================================================
# PARSE VENUE
# ============================================================

def parse_venue(text):

    match = re.search(
        r"(?:Venue|Published in)\s*:\s*(.*?)(?:\n|$)",
        text,
        re.IGNORECASE
    )

    if match:

        return (
            match.group(1)
            .replace("**", "")
            .strip()
        )

    return ""


# ============================================================
# AUTHOR SIMILARITY
# ============================================================

def author_similarity(
    claimed,
    verified
):

    if not claimed or not verified:
        return 0.0

    matched = 0

    for claimed_author in claimed:

        best = 0.0

        for verified_author in verified:

            score = similarity(
                claimed_author,
                verified_author
            )

            best = max(
                best,
                score
            )

        if best >= 75:
            matched += 1

    return (
        matched / len(claimed)
    ) * 100


# ============================================================
# CROSSREF METADATA
# ============================================================

def get_crossref_metadata(doi):

    if not doi:
        return None

    url = (
        f"{CROSSREF_URL}/"
        f"{normalize_doi(doi)}"
    )

    try:

        response = requests.get(
            url,
            timeout=TIMEOUT
        )

        if response.status_code != 200:
            return None

        data = response.json()[
            "message"
        ]

        titles = data.get(
            "title",
            []
        )

        title = (
            titles[0]
            if titles
            else ""
        )

        authors = []

        for author in data.get(
            "author",
            []
        ):

            given = author.get(
                "given",
                ""
            )

            family = author.get(
                "family",
                ""
            )

            name = (
                f"{given} {family}"
            ).strip()

            if name:
                authors.append(
                    name
                )

        year = None

        for field in [
            "published-print",
            "published-online",
            "published",
            "issued",
            "created"
        ]:

            field_data = data.get(
                field
            )

            if not field_data:
                continue

            date_parts = field_data.get(
                "date-parts"
            )

            if (
                date_parts
                and date_parts[0]
            ):

                year = int(
                    date_parts[0][0]
                )

                break

        containers = data.get(
            "container-title",
            []
        )

        if containers:

            venue = containers[0]

        else:

            venue = data.get(
                "publisher",
                ""
            )

        return {
            "title": title,
            "authors": authors,
            "year": year,
            "venue": venue,
            "doi": normalize_doi(
                data.get(
                    "DOI",
                    ""
                )
            )
        }

    except Exception:

        return None


# ============================================================
# VERIFY ONE CITATION
# ============================================================

def verify_citation(
    citation
):

    claimed_title = parse_title(
        citation
    )

    claimed_authors = parse_authors(
        citation
    )

    claimed_year = parse_year(
        citation
    )

    claimed_venue = parse_venue(
        citation
    )

    claimed_doi = extract_doi(
        citation
    )

    metadata = get_crossref_metadata(
        claimed_doi
    )

    # --------------------------------------------------------
    # DOI DOES NOT EXIST
    # --------------------------------------------------------

    if metadata is None:

        return {
            "prediction": 1,
            "doi_exists": False,
            "title_score": 0,
            "author_score": 0,
            "year_match": False,
            "venue_score": 0,
            "doi_match": False
        }

    # --------------------------------------------------------
    # TITLE
    # --------------------------------------------------------

    title_score = title_similarity(
        claimed_title,
        metadata["title"]
    )

    # --------------------------------------------------------
    # AUTHORS
    # --------------------------------------------------------

    author_score = author_similarity(
        claimed_authors,
        metadata["authors"]
    )

    # --------------------------------------------------------
    # YEAR
    # --------------------------------------------------------

    year_match = (
        claimed_year is None
        or metadata["year"] is None
        or claimed_year
        == metadata["year"]
    )

    # --------------------------------------------------------
    # VENUE
    # --------------------------------------------------------

    venue_score = similarity(
        claimed_venue,
        metadata["venue"]
    )

    venue_match = (
        not claimed_venue
        or venue_score
        >= VENUE_THRESHOLD
    )

    # --------------------------------------------------------
    # DOI
    # --------------------------------------------------------

    doi_match = (
        normalize_doi(
            claimed_doi
        )
        ==
        normalize_doi(
            metadata["doi"]
        )
    )

    # --------------------------------------------------------
    # DECISION
    # --------------------------------------------------------

    valid = (
        title_score
        >= TITLE_THRESHOLD
        and
        author_score
        >= AUTHOR_THRESHOLD
        and
        year_match
        and
        venue_match
        and
        doi_match
    )

    prediction = (
        0
        if valid
        else 1
    )

    return {
        "prediction": prediction,
        "doi_exists": True,
        "title_score":
            round(title_score, 2),
        "author_score":
            round(author_score, 2),
        "year_match":
            year_match,
        "venue_score":
            round(venue_score, 2),
        "doi_match":
            doi_match
    }


# ============================================================
# LOAD DATASET
# ============================================================

def load_dataset():

    with open(
        DATASET_FILE,
        "r",
        encoding="utf-8",
        newline=""
    ) as file:

        rows = list(
            csv.DictReader(file)
        )

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

    tp = tn = fp = fn = 0

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
        if total else 0
    )

    precision = (
        tp / (tp + fp)
        if tp + fp else 0
    )

    recall = (
        tp / (tp + fn)
        if tp + fn else 0
    )

    f1 = (
        2 * precision * recall
        / (precision + recall)
        if precision + recall
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
        "CROSSREF METADATA BASELINE"
    )
    print("=" * 70)

    rows = load_dataset()

    print(
        f"\nTesting {len(rows)} citations..."
    )

    y_true = []
    y_pred = []

    output = []

    for index, row in enumerate(
        rows,
        start=1
    ):

        result = verify_citation(
            row["citation"]
        )

        ground_truth = int(
            row["ground_truth"]
        )

        prediction = result[
            "prediction"
        ]

        y_true.append(
            ground_truth
        )

        y_pred.append(
            prediction
        )

        output.append(
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

                "doi_exists":
                    result[
                        "doi_exists"
                    ],

                "title_score":
                    result[
                        "title_score"
                    ],

                "author_score":
                    result[
                        "author_score"
                    ],

                "year_match":
                    result[
                        "year_match"
                    ],

                "venue_score":
                    result[
                        "venue_score"
                    ],

                "doi_match":
                    result[
                        "doi_match"
                    ]
            }
        )

        print(
            f"{index}/{len(rows)} "
            f"Prediction={prediction} "
            f"GroundTruth={ground_truth}"
        )

    metrics = calculate_metrics(
        y_true,
        y_pred
    )

    # ========================================================
    # SAVE
    # ========================================================

    with open(
        RESULTS_FILE,
        "w",
        encoding="utf-8",
        newline=""
    ) as file:

        fieldnames = list(
            output[0].keys()
        )

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()

        writer.writerows(
            output
        )

    # ========================================================
    # RESULTS
    # ========================================================

    print()
    print("=" * 70)
    print(
        "CROSSREF METADATA RESULTS"
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