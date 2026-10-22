import csv
import random
import string
import time
from pathlib import Path

import requests


# ============================================================
# CONFIGURATION
# ============================================================

RANDOM_SEED = 42

VALID_COUNT = 100
FAKE_DOI_COUNT = 100
FAKE_AUTHOR_COUNT = 100
WRONG_YEAR_COUNT = 100
FAKE_VENUE_COUNT = 100
FABRICATED_COUNT = 100

TOTAL_COUNT = (
    VALID_COUNT
    + FAKE_DOI_COUNT
    + FAKE_AUTHOR_COUNT
    + WRONG_YEAR_COUNT
    + FAKE_VENUE_COUNT
    + FABRICATED_COUNT
)

CROSSREF_URL = "https://api.crossref.org/works"

OUTPUT_DIR = Path(__file__).resolve().parent

OUTPUT_FILE = OUTPUT_DIR / "citation_test_dataset.csv"


# ============================================================
# RANDOM SEED
# ============================================================

random.seed(RANDOM_SEED)


# ============================================================
# SEARCH TERMS
# ============================================================

SEARCH_TERMS = [
    "machine learning",
    "deep learning",
    "computer vision",
    "natural language processing",
    "artificial intelligence",
    "data science",
    "medical artificial intelligence",
    "image classification",
    "neural networks",
    "information retrieval",
    "speech recognition",
    "robotics",
    "cybersecurity",
    "large language models",
    "software engineering",
]


# ============================================================
# HTTP SESSION
# ============================================================

session = requests.Session()

session.headers.update(
    {
        "User-Agent": (
            "CiteGuard-Research-Benchmark/1.0 "
            "(mailto:citeguard.research@example.com)"
        )
    }
)


# ============================================================
# TEXT CLEANING
# ============================================================

def clean_text(value):

    if value is None:
        return ""

    value = str(value)

    value = value.replace("\n", " ")
    value = value.replace("\r", " ")

    value = " ".join(
        value.split()
    )

    return value.strip()


# ============================================================
# DOI NORMALIZATION
# ============================================================

def normalize_doi(doi):

    if not doi:
        return ""

    doi = clean_text(doi)

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
# YEAR EXTRACTION
# ============================================================

def extract_year(item):

    date_fields = [
        "published-print",
        "published",
        "issued",
        "created",
    ]

    for field in date_fields:

        date_data = item.get(field)

        if not date_data:
            continue

        parts = date_data.get(
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
            TypeError,
        ):
            pass

    return None


# ============================================================
# AUTHOR EXTRACTION
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
            authors.append(name)

    return authors


# ============================================================
# VENUE EXTRACTION
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

    publisher = clean_text(
        item.get(
            "publisher",
            ""
        )
    )

    return publisher


# ============================================================
# TITLE EXTRACTION
# ============================================================

def extract_title(item):

    titles = item.get(
        "title",
        []
    )

    if not titles:
        return ""

    return clean_text(
        titles[0]
    )


# ============================================================
# BUILD PAPER RECORD
# ============================================================

def build_paper_record(item):

    title = extract_title(item)

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
        item.get("DOI")
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
# FETCH REAL PAPERS FROM CROSSREF
# ============================================================

def fetch_crossref_papers(
    target_count=150
):

    papers = []

    seen_dois = set()

    print()
    print("=" * 70)
    print(
        "FETCHING REAL PAPERS FROM CROSSREF"
    )
    print("=" * 70)

    for term in SEARCH_TERMS:

        if len(papers) >= target_count:
            break

        print(
            f"\nSearching: {term}"
        )

        params = {
            "query": term,
            "rows": 100,
            "select": (
                "DOI,title,author,"
                "published,published-print,"
                "issued,created,"
                "container-title,publisher"
            ),
        }

        try:

            response = session.get(
                CROSSREF_URL,
                params=params,
                timeout=30,
            )

            response.raise_for_status()

            data = response.json()

            items = (
                data
                .get("message", {})
                .get("items", [])
            )

            for item in items:

                paper = build_paper_record(
                    item
                )

                if paper is None:
                    continue

                doi = paper["doi"].lower()

                if doi in seen_dois:
                    continue

                seen_dois.add(doi)

                papers.append(
                    paper
                )

                if len(papers) >= target_count:
                    break

            print(
                "Collected papers:",
                len(papers)
            )

        except Exception as exc:

            print(
                "Crossref request failed:",
                exc
            )

        time.sleep(1)

    print()

    print(
        "Total real papers collected:",
        len(papers)
    )

    return papers


# ============================================================
# FORMAT AUTHORS
# ============================================================

def format_authors(authors):

    return "; ".join(
        authors
    )


# ============================================================
# VALID CITATION
# ============================================================

def create_valid_citation(
    paper
):

    return (
        f'Title: "{paper["title"]}"\n'
        f'Authors: {format_authors(paper["authors"])}\n'
        f'Year: {paper["year"]}\n'
        f'Venue: {paper["venue"]}\n'
        f'DOI: {paper["doi"]}'
    )


# ============================================================
# FAKE DOI
# ============================================================

def create_fake_doi(
    paper
):

    fake_suffix = "".join(
        random.choices(
            string.ascii_lowercase
            + string.digits,
            k=12,
        )
    )

    fake_doi = (
        "10.9999/"
        + fake_suffix
    )

    return (
        f'Title: "{paper["title"]}"\n'
        f'Authors: {format_authors(paper["authors"])}\n'
        f'Year: {paper["year"]}\n'
        f'Venue: {paper["venue"]}\n'
        f'DOI: {fake_doi}'
    )


# ============================================================
# FAKE AUTHORS
# ============================================================

def create_fake_authors(
    paper
):

    fake_authors = list(
        paper["authors"]
    )

    fake_authors[0] = (
        "Jonathan A. Fake"
    )

    return (
        f'Title: "{paper["title"]}"\n'
        f'Authors: {format_authors(fake_authors)}\n'
        f'Year: {paper["year"]}\n'
        f'Venue: {paper["venue"]}\n'
        f'DOI: {paper["doi"]}'
    )


# ============================================================
# WRONG YEAR
# ============================================================

def create_wrong_year(
    paper
):

    wrong_year = (
        paper["year"] + 5
    )

    return (
        f'Title: "{paper["title"]}"\n'
        f'Authors: {format_authors(paper["authors"])}\n'
        f'Year: {wrong_year}\n'
        f'Venue: {paper["venue"]}\n'
        f'DOI: {paper["doi"]}'
    )


# ============================================================
# FAKE VENUE
# ============================================================

def create_fake_venue(
    paper
):

    fake_venue = (
        "International Journal "
        "of Advanced Research "
        "in Artificial Intelligence"
    )

    return (
        f'Title: "{paper["title"]}"\n'
        f'Authors: {format_authors(paper["authors"])}\n'
        f'Year: {paper["year"]}\n'
        f'Venue: {fake_venue}\n'
        f'DOI: {paper["doi"]}'
    )


# ============================================================
# FABRICATED CITATION
# ============================================================

def create_fabricated_citation(
    index
):

    fabricated_title = (
        "A Novel Framework for "
        "Reliable Artificial "
        f"Intelligence Systems "
        f"Part {index}"
    )

    fabricated_authors = (
        "Jonathan A. Smith; "
        "Emily R. Johnson; "
        "Michael K. Brown"
    )

    fabricated_year = random.randint(
        2018,
        2025
    )

    fabricated_venue = (
        "International Journal "
        "of Computational "
        "Intelligence Research"
    )

    fabricated_doi = (
        "10.9999/"
        f"fake.{index:06d}"
    )

    return (
        f'Title: "{fabricated_title}"\n'
        f'Authors: {fabricated_authors}\n'
        f'Year: {fabricated_year}\n'
        f'Venue: {fabricated_venue}\n'
        f'DOI: {fabricated_doi}'
    )


# ============================================================
# BUILD DATASET
# ============================================================

def build_dataset(
    papers
):

    required_real_papers = 100

    if len(papers) < required_real_papers:

        raise RuntimeError(
            "Not enough real papers were "
            "retrieved from Crossref."
        )

    papers = papers[
        :required_real_papers
    ]

    rows = []

    citation_id = 1

    # --------------------------------------------------------
    # VALID CITATIONS
    # --------------------------------------------------------

    for paper in papers:

        citation = (
            create_valid_citation(
                paper
            )
        )

        rows.append(
            {
                "id": citation_id,
                "llm_response": citation,
                "citation": citation,
                "ground_truth": 0,
                "error_type": "valid",
                "source_doi": paper["doi"],
            }
        )

        citation_id += 1

    # --------------------------------------------------------
    # FAKE DOI
    # --------------------------------------------------------

    for paper in papers:

        citation = (
            create_fake_doi(
                paper
            )
        )

        rows.append(
            {
                "id": citation_id,
                "llm_response": citation,
                "citation": citation,
                "ground_truth": 1,
                "error_type": "fake_doi",
                "source_doi": paper["doi"],
            }
        )

        citation_id += 1

    # --------------------------------------------------------
    # FAKE AUTHORS
    # --------------------------------------------------------

    for paper in papers:

        citation = (
            create_fake_authors(
                paper
            )
        )

        rows.append(
            {
                "id": citation_id,
                "llm_response": citation,
                "citation": citation,
                "ground_truth": 1,
                "error_type": "fake_authors",
                "source_doi": paper["doi"],
            }
        )

        citation_id += 1

    # --------------------------------------------------------
    # WRONG YEAR
    # --------------------------------------------------------

    for paper in papers:

        citation = (
            create_wrong_year(
                paper
            )
        )

        rows.append(
            {
                "id": citation_id,
                "llm_response": citation,
                "citation": citation,
                "ground_truth": 1,
                "error_type": "wrong_year",
                "source_doi": paper["doi"],
            }
        )

        citation_id += 1

    # --------------------------------------------------------
    # FAKE VENUE
    # --------------------------------------------------------

    for paper in papers:

        citation = (
            create_fake_venue(
                paper
            )
        )

        rows.append(
            {
                "id": citation_id,
                "llm_response": citation,
                "citation": citation,
                "ground_truth": 1,
                "error_type": "fake_venue",
                "source_doi": paper["doi"],
            }
        )

        citation_id += 1

    # --------------------------------------------------------
    # FABRICATED CITATIONS
    # --------------------------------------------------------

    for index in range(
        1,
        FABRICATED_COUNT + 1
    ):

        citation = (
            create_fabricated_citation(
                index
            )
        )

        rows.append(
            {
                "id": citation_id,
                "llm_response": citation,
                "citation": citation,
                "ground_truth": 1,
                "error_type":
                    "fabricated_citation",
                "source_doi": "",
            }
        )

        citation_id += 1

    # --------------------------------------------------------
    # SHUFFLE DATASET
    # --------------------------------------------------------

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

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    fieldnames = [
        "id",
        "llm_response",
        "citation",
        "ground_truth",
        "error_type",
        "source_doi",
    ]

    with open(
        OUTPUT_FILE,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        writer.writerows(
            rows
        )

    print()
    print("=" * 70)
    print("DATASET CREATED")
    print("=" * 70)

    print(
        f"Rows: {len(rows)}"
    )

    print(
        f"Output: {OUTPUT_FILE}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 70)
    print(
        "CITEGUARD CITATION VERIFICATION BENCHMARK"
    )
    print("=" * 70)

    print(
        f"Target dataset size: {TOTAL_COUNT}"
    )

    papers = fetch_crossref_papers(
        target_count=150
    )

    rows = build_dataset(
        papers
    )

    save_dataset(
        rows
    )

    print()
    print(
        "Ground truth definition:"
    )

    print(
        "0 = Valid citation"
    )

    print(
        "1 = Hallucinated / incorrect citation"
    )

    print()
    print(
        "Error categories:"
    )

    categories = [
        "valid",
        "fake_doi",
        "fake_authors",
        "wrong_year",
        "fake_venue",
        "fabricated_citation",
    ]

    for category in categories:

        count = sum(
            1
            for row in rows
            if row["error_type"]
            == category
        )

        print(
            f"  {category}: {count}"
        )


if __name__ == "__main__":
    main()