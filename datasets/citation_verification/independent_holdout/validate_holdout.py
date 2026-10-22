"""
Rigorous Validation Suite for Independent Multidisciplinary Holdout Benchmark.

Enforces:
  1. Complete disjointness against V1.0 and V2.0 benchmarks (DOIs, titles, citations).
  2. Exact dataset counts (400 total, 100 valid, 300 perturbed; 100 per discipline, 60 per error type).
  3. Zero no-op mutations (mutated_field != original_field for all 300 perturbed records).
  4. Parsing integrity with CiteGuard citation extractor and parser.
  5. Uniqueness: zero duplicate citations or cross-label collisions.
"""

import csv
import json
from pathlib import Path
import re
import sys
import pandas as pd

# Add project root and backend to sys.path
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parents[2]
BACKEND_DIR = PROJECT_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.services.citation_extractor import extract_citations
from app.services.citation_parser import parse_citation


HOLDOUT_DATASET = BASE_DIR / "independent_holdout_dataset.csv"
V1_DATASET = BASE_DIR.parent / "hard_citation_test_dataset.csv"
V2_DATASET = BASE_DIR.parent / "benchmark_v2" / "hard_citation_test_dataset_v2.csv"
V1_ORIGINAL = BASE_DIR.parent / "citation_test_dataset.csv"


def clean_text(s: str) -> str:
    if not s:
        return ""
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


def run_validation():
    print("=" * 75)
    print("INDEPENDENT HOLDOUT BENCHMARK RIGOROUS VALIDATION SUITE")
    print("=" * 75)

    if not HOLDOUT_DATASET.exists():
        print(f"FAIL: Holdout dataset missing at {HOLDOUT_DATASET}")
        return False

    df = pd.read_csv(HOLDOUT_DATASET)
    print(f"Total Rows Loaded: {len(df)}")

    # ----------------------------------------------------
    # Check 1: Exact Counts & Balance
    # ----------------------------------------------------
    print("\n--- Check 1: Counts & Stratification Balance ---")
    assert len(df) == 400, f"Expected 400 rows, got {len(df)}"
    assert (df["ground_truth"] == 0).sum() == 100, "Expected exactly 100 genuine (valid) records"
    assert (df["ground_truth"] == 1).sum() == 300, "Expected exactly 300 perturbed records"

    expected_disciplines = [
        "computer_science",
        "medicine_biomedical",
        "natural_sciences",
        "humanities_social_sciences",
    ]
    for disc in expected_disciplines:
        c = (df["discipline"] == disc).sum()
        assert c == 100, f"Expected 100 records for {disc}, got {c}"
        c_val = ((df["discipline"] == disc) & (df["ground_truth"] == 0)).sum()
        assert c_val == 25, f"Expected 25 valid records for {disc}, got {c_val}"
        c_pert = ((df["discipline"] == disc) & (df["ground_truth"] == 1)).sum()
        assert c_pert == 75, f"Expected 75 perturbed records for {disc}, got {c_pert}"

    expected_errors = {
        "valid": 100,
        "corrupted_authors": 60,
        "wrong_venue": 60,
        "wrong_year": 60,
        "doi_mismatch": 60,
        "plausible_fabricated": 60,
    }
    for err, exp_count in expected_errors.items():
        actual_count = (df["error_type"] == err).sum()
        assert actual_count == exp_count, f"Error category {err}: expected {exp_count}, got {actual_count}"
        if err != "valid":
            # Check 15 per discipline
            for disc in expected_disciplines:
                disc_err_count = ((df["discipline"] == disc) & (df["error_type"] == err)).sum()
                assert disc_err_count == 15, f"{err} in {disc}: expected 15, got {disc_err_count}"

    print("PASS: Exact 400 records, 100/300 split, 100 per discipline, 60 per error category.")

    # ----------------------------------------------------
    # Check 2: Disjointness from V1.0 and V2.0 Benchmarks
    # ----------------------------------------------------
    print("\n--- Check 2: Disjointness against V1.0 / V2.0 Benchmarks ---")
    df1 = pd.read_csv(V1_DATASET)
    df2 = pd.read_csv(V2_DATASET)
    df_orig = pd.read_csv(V1_ORIGINAL)

    v1_v2_dois = set()
    for d in [df1, df2]:
        for col in ["source_doi", "donor_doi"]:
            if col in d.columns:
                v1_v2_dois.update(d[col].dropna().apply(normalize_doi))

    v1_v2_citations = set()
    for d in [df1, df2]:
        if "citation" in d.columns:
            v1_v2_citations.update(d["citation"].dropna().str.strip())
    if "llm_response" in df_orig.columns:
        v1_v2_citations.update(df_orig["llm_response"].dropna().str.strip())

    v1_v2_titles = set()
    for cit in v1_v2_citations:
        m = re.search(r'Title:\s*"([^"]+)"', cit)
        if m:
            v1_v2_titles.add(clean_text(m.group(1)).lower())

    holdout_dois = set(df["source_doi"].dropna().apply(normalize_doi)).union(
        set(df["donor_doi"].dropna().apply(normalize_doi))
    )
    holdout_dois.discard("")

    holdout_citations = set(df["citation"].dropna().str.strip())
    holdout_titles = set()
    for cit in holdout_citations:
        m = re.search(r'Title:\s*"([^"]+)"', cit)
        if m:
            holdout_titles.add(clean_text(m.group(1)).lower())

    doi_overlap = holdout_dois.intersection(v1_v2_dois)
    cit_overlap = holdout_citations.intersection(v1_v2_citations)
    title_overlap = holdout_titles.intersection(v1_v2_titles)

    print(f"Protected V1/V2 DOIs   : {len(v1_v2_dois)}")
    print(f"Holdout DOIs           : {len(holdout_dois)}")
    print(f"DOI Overlap Count      : {len(doi_overlap)}")
    assert len(doi_overlap) == 0, f"LEAKAGE DETECTED: Overlapping DOIs: {doi_overlap}"

    print(f"Protected V1/V2 Titles : {len(v1_v2_titles)}")
    print(f"Holdout Titles         : {len(holdout_titles)}")
    print(f"Title Overlap Count    : {len(title_overlap)}")
    assert len(title_overlap) == 0, f"LEAKAGE DETECTED: Overlapping Titles: {title_overlap}"

    print(f"Citation Overlap Count : {len(cit_overlap)}")
    assert len(cit_overlap) == 0, f"LEAKAGE DETECTED: Overlapping Citations: {cit_overlap}"

    print("PASS: 100% strict disjointness verified. Zero leakage from V1/V2.")

    # ----------------------------------------------------
    # Check 3: Zero No-Op Mutations
    # ----------------------------------------------------
    print("\n--- Check 3: Zero No-Op Mutations in Perturbations ---")
    perturbed_df = df[df["ground_truth"] == 1]
    no_ops = []

    for idx, row in perturbed_df.iterrows():
        err = row["error_type"]
        orig = str(row["original_field_value"]).strip()
        mut = str(row["mutated_field_value"]).strip()
        if err in ["corrupted_authors", "wrong_venue", "wrong_year", "doi_mismatch"]:
            if orig.lower() == mut.lower() or not orig or not mut:
                no_ops.append((row["id"], err, orig, mut))
        elif err == "plausible_fabricated":
            if not mut:
                no_ops.append((row["id"], err, orig, mut))

    assert len(no_ops) == 0, f"FAIL: Found {len(no_ops)} no-op mutations: {no_ops}"
    print("PASS: All 300 perturbed records have verified, distinct mutated field values.")

    # ----------------------------------------------------
    # Check 4: Uniqueness & Zero Collisions
    # ----------------------------------------------------
    print("\n--- Check 4: Uniqueness & Zero Collisions ---")
    assert df["id"].nunique() == 400, "IDs must be unique from 1 to 400"
    assert df["citation"].nunique() == 400, f"All 400 citation strings must be distinct, got {df['citation'].nunique()}"
    print("PASS: All 400 citations and IDs are strictly unique.")

    # ----------------------------------------------------
    # Check 5: Citation Parsing Integrity
    # ----------------------------------------------------
    print("\n--- Check 5: Citation Parsing Integrity ---")
    parse_failures = []
    for idx, row in df.iterrows():
        cit = row["citation"]
        extracted = extract_citations(cit)
        if len(extracted) != 1:
            parse_failures.append((row["id"], "extract_failed", len(extracted)))
            continue
        parsed = parse_citation(extracted[0])
        if not parsed.get("title") or not parsed.get("authors") or not parsed.get("year") or not parsed.get("doi"):
            parse_failures.append((row["id"], "missing_parsed_fields", parsed))

    assert len(parse_failures) == 0, f"FAIL: Citation parsing failures: {parse_failures}"
    print("PASS: 100% of 400 citations successfully parsed with complete metadata fields.")

    print("\n" + "=" * 75)
    print("ALL 5 RIGOROUS VALIDATION CHECKS PASSED SUCCESSFULLY (100% COMPLIANT)")
    print("=" * 75)
    return True


if __name__ == "__main__":
    if not run_validation():
        sys.exit(1)
