"""
Compile canonical content-addressed offline cache for Benchmark V2.0.

This script maps each citation in hard_citation_test_dataset_v2.csv to its exact
retrieval evidence from the frozen V1.0 cache:
  - DOIs mapped by normalized DOI (100% coverage).
  - Titles mapped by normalized title (100% coverage).
  - Output is isolated inside benchmark_v2/reproducible_api_cache_v2.json.
  - Features hard path guards preventing writes to any V1.0 artifact.
"""

import json
from pathlib import Path
import re
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
V1_DATASET = BASE_DIR / "hard_citation_test_dataset.csv"
V1_CACHE = BASE_DIR / "reproducible_api_cache.json"

V2_DIR = BASE_DIR / "benchmark_v2"
V2_DATASET = V2_DIR / "hard_citation_test_dataset_v2.csv"
V2_CACHE = V2_DIR / "reproducible_api_cache_v2.json"

# Prohibited V1 targets
FROZEN_V1_PATHS = {
    V1_DATASET,
    V1_CACHE,
    BASE_DIR / "targeted_fixes_results.csv",
    BASE_DIR / "final_results.csv",
}


def assert_path_safety(target_path: Path):
    resolved = target_path.resolve()
    for frozen in FROZEN_V1_PATHS:
        if resolved == frozen.resolve():
            raise PermissionError(f"FATAL: Attempted to write to frozen V1 artifact: {resolved}")
    if "benchmark_v2" not in str(resolved):
        raise PermissionError(f"FATAL: Target path {resolved} is not inside benchmark_v2/.")


def normalize_doi(doi: str) -> str:
    if not doi:
        return ""
    doi = str(doi).strip().lower()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if doi.startswith(prefix):
            doi = doi[len(prefix):]
    return doi.strip().lower()


def clean_title(title: str) -> str:
    if not title:
        return ""
    return " ".join(str(title).split()).strip().lower()


def build_cache_v2():
    assert_path_safety(V2_CACHE)

    print("Loading V1 dataset and frozen API cache...")
    v1_df = pd.read_csv(V1_DATASET)
    with open(V1_CACHE, "r", encoding="utf-8") as f:
        v1_cache = json.load(f)

    # Build content-addressed dictionaries from V1 cache
    doi_store = {}
    title_store = {}

    for idx, row in v1_df.iterrows():
        cid = str(row["id"])
        if cid not in v1_cache:
            continue
        entry = v1_cache[cid]
        cit = row["citation"]

        t_match = re.search(r'Title:\s*"([^"]+)"', cit)
        d_match = re.search(r"DOI:\s*(.+)", cit)

        if d_match:
            d = normalize_doi(d_match.group(1))
            if d and entry.get("verify_doi") is not None:
                doi_store[d] = entry["verify_doi"]

        if t_match:
            t = clean_title(t_match.group(1))
            if t and entry.get("retrieve_candidates") is not None:
                title_store[t] = entry["retrieve_candidates"]

    print(f"Indexed {len(doi_store)} distinct DOIs and {len(title_store)} distinct titles from V1 cache.")

    # Now populate V2 cache keyed by V2 record ID (1 to 600)
    print("Mapping V2 dataset entries to content-addressed cache...")
    v2_df = pd.read_csv(V2_DATASET)
    v2_cache = {}

    hits_doi = 0
    hits_title = 0

    for idx, row in v2_df.iterrows():
        cid = str(row["id"])
        cit = row["citation"]

        t_match = re.search(r'Title:\s*"([^"]+)"', cit)
        d_match = re.search(r"DOI:\s*(.+)", cit)

        d = normalize_doi(d_match.group(1)) if d_match else ""
        t = clean_title(t_match.group(1)) if t_match else ""

        # DOI verification result
        # For synthetic DOIs (10.9999/citeguard.synthetic.*), verify_doi is None as on live Crossref
        doi_result = doi_store.get(d, None)
        if doi_result is not None or d.startswith("10.9999/citeguard.synthetic."):
            hits_doi += 1

        # Title candidates result
        candidates_result = title_store.get(t, [])
        if t in title_store:
            hits_title += 1

        v2_cache[cid] = {
            "verify_doi": doi_result,
            "retrieve_candidates": candidates_result,
            "doi_queried": d,
            "title_queried": t,
        }

    print(f"V2 Cache DOI coverage: {hits_doi} / {len(v2_df)} ({hits_doi/len(v2_df)*100:.1f}%)")
    print(f"V2 Cache Title coverage: {hits_title} / {len(v2_df)} ({hits_title/len(v2_df)*100:.1f}%)")

    assert hits_doi == len(v2_df), "Failed to achieve 100% DOI cache coverage"
    assert hits_title == len(v2_df), "Failed to achieve 100% Title cache coverage"

    with open(V2_CACHE, "w", encoding="utf-8") as f:
        json.dump(v2_cache, f, indent=2)

    print(f"Successfully saved Benchmark V2.0 offline cache to: {V2_CACHE}")


if __name__ == "__main__":
    build_cache_v2()
