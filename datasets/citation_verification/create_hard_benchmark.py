import csv
import random
import re
import time
import requests
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

RANDOM_SEED = 42

COUNT_PER_CATEGORY = 100
TOTAL_COUNT = 600

CROSSREF_URL = "https://api.crossref.org/works"

OUTPUT_FILE = (
    Path(__file__).resolve().parent
    / "hard_citation_test_dataset.csv"
)

TIMEOUT = 20

# We only need 100 real papers.
# Each real paper can be used to create
# multiple controlled test cases.
MIN_REAL_PAPERS = 100

random.seed(RANDOM_SEED)


# ============================================================
# SEARCH TOPICS
# ============================================================

SEARCH_TERMS = [
    "machine learning",
    "deep learning",
    "computer vision",
    "natural language processing",
    "artificial intelligence",
    "neural networks",
    "data mining",
    "information retrieval",
    "image classification",
    "speech recognition",
    "robotics",
    "medical imaging",
    "computer security",
    "software engineering",
    "large language models",
]


# ============================================================
# CROSSREF SESSION
# ============================================================

session = requests.Session()

session.headers.update({
    "User-Agent": (
        "CiteGuard-Hard-Benchmark/1.0 "
        "(research citation verification)"
    )
})


# ============================================================
# NORMALIZE DOI
# ============================================================

def normalize_doi(doi):

    if not doi:
        return ""

    doi = str(doi).strip()

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

    return doi.strip().lower()


# ============================================================
# CLEAN TEXT
# ============================================================

def clean_text(value):

    if value is None:
        return ""

    value = str(value)

    value = value.replace(
        "\n",
        " "
    )

    value = value.replace(
        "\r",
        " "
    )

    return " ".join(
        value.split()
    ).strip()


# ============================================================
# EXTRACT YEAR
# ============================================================

def extract_year(item):

    fields = [
        "published-print",
        "published-online",
        "published",
        "issued",
        "created",
    ]

    for field in fields:

        data = item.get(field)

        if not data:
            continue

        parts = data.get(
            "date-parts"
        )

        if not parts:
            continue

        if not parts[0]:
            continue

        try:

            year = int(
                parts[0][0]
            )

            if 1800 <= year <= 2100:
                return year

        except (
            ValueError,
            TypeError
        ):

            pass

    return None


# ============================================================
# EXTRACT AUTHORS
# ============================================================

def extract_authors(item):

    authors = []

    for author in item.get(
        "author",
        []
    ):

        given = clean_text(
            author.get(
                "given",
                ""
            )
        )

        family = clean_text(
            author.get(
                "family",
                ""
            )
        )

        if given and family:

            name = (
                f"{given} {family}"
            )

        elif family:

            name = family

        elif given:

            name = given

        else:

            name = ""

        if name:
            authors.append(
                name
            )

    return authors


# ============================================================
# EXTRACT VENUE
# ============================================================

def extract_venue(item):

    containers = item.get(
        "container-title",
        []
    )

    if containers:

        return clean_text(
            containers[0]
        )

    return clean_text(
        item.get(
            "publisher",
            ""
        )
    )


# ============================================================
# CONVERT CROSSREF ITEM
# ============================================================

def convert_item(item):

    titles = item.get(
        "title",
        []
    )

    if not titles:
        return None

    title = clean_text(
        titles[0]
    )

    authors = extract_authors(
        item
    )

    year = extract_year(
        item
    )

    venue = extract_venue(
        item
    )

    doi = normalize_doi(
        item.get(
            "DOI",
            ""
        )
    )

    if not title:
        return None

    if not authors:
        return None

    if not year:
        return None

    if not venue:
        return None

    if not doi:
        return None

    return {
        "title": title,
        "authors": authors,
        "year": year,
        "venue": venue,
        "doi": doi,
    }


# ============================================================
# FETCH REAL PAPERS
# ============================================================

def fetch_real_papers(
    target=110
):

    papers = []

    seen_dois = set()

    print()
    print("=" * 70)
    print(
        "COLLECTING REAL CROSSREF PAPERS"
    )
    print("=" * 70)

    for term in SEARCH_TERMS:

        if len(papers) >= target:
            break

        print(
            f"\nSearching: {term}"
        )

        params = {
            "query": term,
            "rows": 50,
            "select": (
                "DOI,title,author,"
                "published,published-print,"
                "published-online,issued,created,"
                "container-title,publisher"
            ),
        }

        # ----------------------------------------------------
        # Retry Crossref when rate limited
        # ----------------------------------------------------

        success = False

        for attempt in range(4):

            try:

                response = session.get(
                    CROSSREF_URL,
                    params=params,
                    timeout=TIMEOUT
                )

                if response.status_code == 429:

                    wait_time = (
                        5 * (attempt + 1)
                    )

                    print(
                        "Crossref rate limit reached."
                    )

                    print(
                        f"Waiting {wait_time} seconds..."
                    )

                    time.sleep(
                        wait_time
                    )

                    continue

                response.raise_for_status()

                success = True

                break

            except Exception as exc:

                if attempt == 3:

                    print(
                        "Crossref request failed:",
                        exc
                    )

                else:

                    wait_time = (
                        3 * (attempt + 1)
                    )

                    print(
                        f"Retrying in {wait_time} seconds..."
                    )

                    time.sleep(
                        wait_time
                    )

        if not success:
            continue

        # ----------------------------------------------------
        # Process response
        # ----------------------------------------------------

        try:

            items = (
                response.json()
                .get("message", {})
                .get("items", [])
            )

        except Exception as exc:

            print(
                "Could not read Crossref response:",
                exc
            )

            continue

        for item in items:

            paper = convert_item(
                item
            )

            if paper is None:
                continue

            doi = paper["doi"]

            if doi in seen_dois:
                continue

            seen_dois.add(
                doi
            )

            papers.append(
                paper
            )

            if len(papers) >= target:
                break

        print(
            "Collected:",
            len(papers)
        )

        # Small delay between Crossref requests
        time.sleep(1.5)

    print()
    print(
        "Real papers collected:",
        len(papers)
    )

    return papers


# ============================================================
# FORMAT AUTHORS
# ============================================================

def format_authors(
    authors
):

    return "; ".join(
        authors
    )


# ============================================================
# FORMAT CITATION
# ============================================================

def format_citation(
    title,
    authors,
    year,
    venue,
    doi
):

    return (
        f'Title: "{title}"\n'
        f'Authors: {format_authors(authors)}\n'
        f'Year: {year}\n'
        f'Venue: {venue}\n'
        f'DOI: {doi}'
    )


# ============================================================
# 1. VALID CITATION
# ============================================================

def make_valid(
    paper
):

    return format_citation(
        paper["title"],
        paper["authors"],
        paper["year"],
        paper["venue"],
        paper["doi"]
    )


# ============================================================
# 2. DOI MISMATCH
# ============================================================

def make_doi_mismatch(
    paper,
    other_paper
):

    return format_citation(
        paper["title"],
        paper["authors"],
        paper["year"],
        paper["venue"],
        other_paper["doi"]
    )


# ============================================================
# 3. CORRUPTED AUTHORS
# ============================================================

def make_corrupted_authors(
    paper,
    replacement_paper
):

    authors = list(
        paper["authors"]
    )

    replacement_authors = (
        replacement_paper["authors"]
    )

    if not authors:
        authors = list(
            replacement_authors
        )

    elif replacement_authors:

        # Replace exactly one author
        # with a real author from another
        # real paper.

        authors[0] = (
            replacement_authors[0]
        )

    return format_citation(
        paper["title"],
        authors,
        paper["year"],
        paper["venue"],
        paper["doi"]
    )


# ============================================================
# 4. WRONG YEAR
# ============================================================

def make_wrong_year(
    paper
):

    original_year = paper["year"]

    # Make a plausible year error.
    # Alternate between +1 and -1.

    if original_year % 2 == 0:

        wrong_year = (
            original_year + 1
        )

    else:

        wrong_year = (
            original_year - 1
        )

    # Keep within a reasonable range.

    if wrong_year < 1800:

        wrong_year = (
            original_year + 2
        )

    return format_citation(
        paper["title"],
        paper["authors"],
        wrong_year,
        paper["venue"],
        paper["doi"]
    )


# ============================================================
# 5. WRONG VENUE
# ============================================================

def make_wrong_venue(
    paper,
    replacement_paper
):

    return format_citation(
        paper["title"],
        paper["authors"],
        paper["year"],
        replacement_paper["venue"],
        paper["doi"]
    )


# ============================================================
# 6. PLAUSIBLE FABRICATED CITATION
# ============================================================

def make_fabricated(
    index
):

    titles = [
        "A Unified Framework for Reliable Citation Verification",
        "Detecting Hallucinated References in Neural Language Models",
        "Context Aware Verification of Automatically Generated Citations",
        "A Robust Method for Scholarly Reference Validation",
        "Semantic Verification of Research Citations Generated by Language Models",
        "Automated Detection of Fabricated Academic References",
        "Multi Source Verification of AI Generated Bibliographic Information",
        "Reliable Citation Grounding for Large Language Models",
        "A Deep Learning Framework for Academic Citation Validation",
        "Neural Verification of Automatically Generated Scholarly References",
    ]

    author_sets = [
        [
            "Daniel Anderson",
            "Michael Roberts"
        ],
        [
            "Sophia Williams",
            "James Carter"
        ],
        [
            "Robert Miller",
            "Emma Thompson"
        ],
        [
            "David Wilson",
            "Olivia Martin"
        ],
        [
            "Andrew Johnson",
            "Emily Davis"
        ],
    ]

    venues = [
        "Journal of Artificial Intelligence Research",
        "International Journal of Computer Vision",
        "IEEE Transactions on Artificial Intelligence",
        "ACM Transactions on Intelligent Systems and Technology",
        "Information Processing and Management",
    ]

    title = (
        random.choice(titles)
        + f" ({index})"
    )

    authors = random.choice(
        author_sets
    )

    year = random.randint(
        2018,
        2024
    )

    venue = random.choice(
        venues
    )

    # Intentionally nonexistent DOI.
    doi = (
        "10.9999/"
        f"citeguard.synthetic."
        f"{index:04d}"
    )

    return format_citation(
        title,
        authors,
        year,
        venue,
        doi
    )


# ============================================================
# BUILD DATASET
# ============================================================

def build_dataset(
    papers
):

    if len(papers) < MIN_REAL_PAPERS:

        raise RuntimeError(
            f"Only {len(papers)} real papers "
            f"were collected. "
            f"Need at least {MIN_REAL_PAPERS}."
        )

    # --------------------------------------------------------
    # Use exactly 100 real papers.
    # --------------------------------------------------------

    papers = papers[
        :MIN_REAL_PAPERS
    ]

    rows = []

    row_id = 1

    # ========================================================
    # CATEGORY 1 — VALID
    # ========================================================

    for i in range(
        COUNT_PER_CATEGORY
    ):

        paper = papers[i]

        citation = make_valid(
            paper
        )

        rows.append({
            "id": row_id,
            "citation": citation,
            "ground_truth": 0,
            "error_type": "valid",
            "source_doi": paper["doi"],
            "description":
                "Unmodified real citation"
        })

        row_id += 1

    # ========================================================
    # CATEGORY 2 — DOI MISMATCH
    # ========================================================

    for i in range(
        COUNT_PER_CATEGORY
    ):

        paper = papers[i]

        # Pick a different real paper.
        other = papers[
            (i + 1) % MIN_REAL_PAPERS
        ]

        citation = make_doi_mismatch(
            paper,
            other
        )

        rows.append({
            "id": row_id,
            "citation": citation,
            "ground_truth": 1,
            "error_type":
                "doi_mismatch",
            "source_doi":
                paper["doi"],
            "description":
                "Correct metadata paired with DOI belonging to another real paper"
        })

        row_id += 1

    # ========================================================
    # CATEGORY 3 — CORRUPTED AUTHORS
    # ========================================================

    for i in range(
        COUNT_PER_CATEGORY
    ):

        paper = papers[i]

        replacement = papers[
            (i + 1) % MIN_REAL_PAPERS
        ]

        citation = make_corrupted_authors(
            paper,
            replacement
        )

        rows.append({
            "id": row_id,
            "citation": citation,
            "ground_truth": 1,
            "error_type":
                "corrupted_authors",
            "source_doi":
                paper["doi"],
            "description":
                "One author replaced with a real author from another paper"
        })

        row_id += 1

    # ========================================================
    # CATEGORY 4 — WRONG YEAR
    # ========================================================

    for i in range(
        COUNT_PER_CATEGORY
    ):

        paper = papers[i]

        citation = make_wrong_year(
            paper
        )

        rows.append({
            "id": row_id,
            "citation": citation,
            "ground_truth": 1,
            "error_type":
                "wrong_year",
            "source_doi":
                paper["doi"],
            "description":
                "Real citation with a plausible incorrect publication year"
        })

        row_id += 1

    # ========================================================
    # CATEGORY 5 — WRONG VENUE
    # ========================================================

    for i in range(
        COUNT_PER_CATEGORY
    ):

        paper = papers[i]

        replacement = papers[
            (i + 1) % MIN_REAL_PAPERS
        ]

        citation = make_wrong_venue(
            paper,
            replacement
        )

        rows.append({
            "id": row_id,
            "citation": citation,
            "ground_truth": 1,
            "error_type":
                "wrong_venue",
            "source_doi":
                paper["doi"],
            "description":
                "Real citation with venue replaced by another real venue"
        })

        row_id += 1

    # ========================================================
    # CATEGORY 6 — PLAUSIBLE FABRICATION
    # ========================================================

    for i in range(
        1,
        COUNT_PER_CATEGORY + 1
    ):

        citation = make_fabricated(
            i
        )

        rows.append({
            "id": row_id,
            "citation": citation,
            "ground_truth": 1,
            "error_type":
                "plausible_fabricated",
            "source_doi": "",
            "description":
                "Plausible-looking fabricated scholarly citation"
        })

        row_id += 1

    # ========================================================
    # VERIFY SIZE
    # ========================================================

    if len(rows) != TOTAL_COUNT:

        raise RuntimeError(
            f"Expected {TOTAL_COUNT} rows "
            f"but generated {len(rows)}."
        )

    # ========================================================
    # SHUFFLE
    # ========================================================

    random.shuffle(
        rows
    )

    return rows


# ============================================================
# SAVE DATASET
# ============================================================

def save_dataset(
    rows
):

    fieldnames = [
        "id",
        "citation",
        "ground_truth",
        "error_type",
        "source_doi",
        "description",
    ]

    with open(
        OUTPUT_FILE,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()

        writer.writerows(
            rows
        )

    print()
    print("=" * 70)
    print(
        "HARD BENCHMARK CREATED"
    )
    print("=" * 70)

    print(
        f"Total rows: {len(rows)}"
    )

    print(
        f"Output: {OUTPUT_FILE}"
    )

    print()

    counts = {}

    for row in rows:

        category = row[
            "error_type"
        ]

        counts[category] = (
            counts.get(
                category,
                0
            ) + 1
        )

    print(
        "CATEGORY COUNTS"
    )

    print(
        "-" * 70
    )

    for category, count in sorted(
        counts.items()
    ):

        print(
            f"{category}: {count}"
        )

    print()

    print(
        "Ground truth:"
    )

    print(
        "0 = Valid citation"
    )

    print(
        "1 = Hallucinated / incorrect citation"
    )

    print(
        "=" * 70
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 70)
    print(
        "CITEGUARD HARD BENCHMARK"
    )
    print("=" * 70)

    print()
    print(
        "Target dataset size:",
        TOTAL_COUNT
    )

    print(
        "Real papers required:",
        MIN_REAL_PAPERS
    )

    # We only need 110 because Crossref may
    # reject some records during processing.

    papers = fetch_real_papers(
        target=110
    )

    if len(papers) < MIN_REAL_PAPERS:

        print()
        print(
            "ERROR:"
        )

        print(
            f"Only {len(papers)} valid papers "
            "were collected."
        )

        print(
            f"At least {MIN_REAL_PAPERS} "
            "are required."
        )

        print(
            "Please run the script again "
            "after Crossref rate limiting clears."
        )

        return

    rows = build_dataset(
        papers
    )

    save_dataset(
        rows
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()