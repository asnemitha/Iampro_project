"""
Harvest and Verify 100 Multidisciplinary Seed Papers from Crossref.

Disciplines:
  1. computer_science (25 papers)
  2. medicine_biomedical (25 papers)
  3. natural_sciences (25 papers)
  4. humanities_social_sciences (25 papers)

Enforces 100% disjointness from V1.0 and V2.0 benchmarks.
"""

import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
import time
import requests
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parents[2]
HOLDOUT_DIR = BASE_DIR

# Protected V1 / V2 paths
V1_DATASET = BASE_DIR.parent / "hard_citation_test_dataset.csv"
V2_DATASET = BASE_DIR.parent / "benchmark_v2" / "hard_citation_test_dataset_v2.csv"
V1_ORIGINAL = BASE_DIR.parent / "citation_test_dataset.csv"


def load_excluded_provenance():
    df1 = pd.read_csv(V1_DATASET)
    df2 = pd.read_csv(V2_DATASET)
    df_orig = pd.read_csv(V1_ORIGINAL)

    excluded_dois = set()
    for col in ["source_doi", "donor_doi"]:
        if col in df1.columns:
            excluded_dois.update(df1[col].dropna().astype(str).str.lower().str.strip())
        if col in df2.columns:
            excluded_dois.update(df2[col].dropna().astype(str).str.lower().str.strip())

    excluded_citations = set()
    if "citation" in df1.columns:
        excluded_citations.update(df1["citation"].dropna().astype(str).str.strip())
    if "citation" in df2.columns:
        excluded_citations.update(df2["citation"].dropna().astype(str).str.strip())
    if "llm_response" in df_orig.columns:
        excluded_citations.update(df_orig["llm_response"].dropna().astype(str).str.strip())

    excluded_titles = set()
    for cit in excluded_citations:
        m = re.search(r'Title:\s*"([^"]+)"', cit)
        if m:
            excluded_titles.add(clean_text(m.group(1)).lower())

    print(f"Loaded {len(excluded_dois)} excluded DOIs and {len(excluded_titles)} excluded titles from V1/V2.")
    return excluded_dois, excluded_titles, excluded_citations


def clean_text(s: str) -> str:
    if not s:
        return ""
    # Strip HTML tags
    s = re.sub(r"<[^>]+>", "", str(s))
    return " ".join(s.replace("\n", " ").replace("\r", " ").split()).strip()


def normalize_doi(doi: str) -> str:
    if not doi:
        return ""
    doi = str(doi).strip().lower()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if doi.startswith(prefix):
            doi = doi[len(prefix):]
    return doi.strip().lower()


DISCIPLINE_QUERIES = {
    "computer_science": [
        "cryptography zero knowledge protocols",
        "distributed consensus Byzantine fault tolerance",
        "relational database query optimization indexing",
        "software architecture refactoring static analysis",
        "wireless sensor network routing protocols",
    ],
    "medicine_biomedical": [
        "cardiovascular disease randomized double-blind trial",
        "targeted immunotherapy monoclonal antibodies oncology",
        "type 2 diabetes glycemic control metformin trial",
        "Alzheimer disease amyloid tau biomarkers neurology",
        "antibiotic resistance genomic epidemiology bacteriology",
    ],
    "natural_sciences": [
        "gravitational waves binary black hole merger astrophysics",
        "topological insulators quantum Hall effect condensed matter",
        "homogeneous catalysis organometallic reaction mechanisms",
        "CRISPR Cas9 gene editing plant physiology",
        "ocean acidification coral reef carbonate chemistry",
    ],
    "humanities_social_sciences": [
        "monetary policy inflation expectations Phillips curve economics",
        "working memory cognitive cognitive load theory psychology",
        "social mobility educational attainment intergenerational inequality",
        "phonological acquisition syntax semantics syntax linguistics",
        "historical sociology institutional change democratization",
    ],
}


def harvest_discipline_seeds(discipline: str, excluded_dois: set, excluded_titles: set, target_count: int = 25):
    headers = {"User-Agent": "CiteGuard-Holdout-Research/1.0 (mailto:citeguard.research@gmail.com)"}
    queries = DISCIPLINE_QUERIES[discipline]
    seeds = []
    seen_dois = set()
    seen_titles = set()

    for q in queries:
        if len(seeds) >= target_count:
            break
        url = f"https://api.crossref.org/works?query={requests.utils.quote(q)}&rows=30&filter=type:journal-article"
        try:
            r = requests.get(url, headers=headers, timeout=12)
            if r.status_code != 200:
                print(f"Warning: HTTP {r.status_code} for query: {q}")
                continue
            items = r.json().get("message", {}).get("items", [])
        except Exception as e:
            print(f"Error querying {q}: {e}")
            continue

        for item in items:
            if len(seeds) >= target_count:
                break

            raw_doi = item.get("DOI", "")
            norm_doi = normalize_doi(raw_doi)
            if not norm_doi or norm_doi in excluded_dois or norm_doi in seen_dois:
                continue

            raw_title = item.get("title", [""])[0] if item.get("title") else ""
            title = clean_text(raw_title)
            norm_title = title.lower()
            if not title or len(title) < 15 or len(title.split()) < 3:
                continue
            if norm_title in excluded_titles or norm_title in seen_titles:
                continue

            # Check authors
            author_items = item.get("author", [])
            if not author_items or len(author_items) < 1:
                continue

            authors = []
            for a in author_items:
                given = clean_text(a.get("given", ""))
                family = clean_text(a.get("family", ""))
                if family and given:
                    authors.append(f"{given} {family}")
                elif family:
                    authors.append(family)

            if not authors:
                continue

            # Check year
            issued = item.get("issued", {}).get("date-parts", [[None]])[0]
            year = issued[0] if issued and len(issued) > 0 else None
            if not year or not isinstance(year, int) or year < 2000 or year > 2024:
                continue

            # Check venue
            venues = item.get("container-title", [])
            venue = clean_text(venues[0]) if venues else ""
            if not venue or len(venue) < 3:
                continue

            # Passed all quality checks!
            seed_record = {
                "discipline": discipline,
                "doi": norm_doi,
                "title": title,
                "authors": authors,
                "year": year,
                "venue": venue,
                "source": "Crossref",
                "retrieval_date": datetime.now(timezone.utc).isoformat(),
            }
            seeds.append(seed_record)
            seen_dois.add(norm_doi)
            seen_titles.add(norm_title)
            time.sleep(0.05)

    print(f"[{discipline}] Harvested {len(seeds)} / {target_count} validated seeds.")
    return seeds


def main():
    print("=" * 70)
    print("HARVESTING MULTIDISCIPLINARY SEEDS FOR INDEPENDENT HOLDOUT BENCHMARK")
    print("=" * 70)

    excluded_dois, excluded_titles, _ = load_excluded_provenance()

    all_seeds = []
    disciplines = [
        "computer_science",
        "medicine_biomedical",
        "natural_sciences",
        "humanities_social_sciences",
    ]

    for disc in disciplines:
        seeds = harvest_discipline_seeds(disc, excluded_dois, excluded_titles, target_count=25)
        if len(seeds) < 25:
            print(f"ERROR: Could only find {len(seeds)} valid seeds for {disc}! Shortfall reported.")
            sys.exit(1)
        all_seeds.extend(seeds)

    output_path = HOLDOUT_DIR / "multidisciplinary_seed_papers.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_seeds, f, indent=2)

    print(f"\n[SUCCESS] Successfully harvested and verified {len(all_seeds)} distinct seeds.")
    print(f"Saved to: {output_path}")

    # Summary breakdown
    df = pd.DataFrame(all_seeds)
    print("\nBreakdown by Discipline:")
    print(df["discipline"].value_counts())
    print("\nYear Range:", df["year"].min(), "to", df["year"].max())
    print("Total Unique DOIs:", df["doi"].nunique())


if __name__ == "__main__":
    main()
