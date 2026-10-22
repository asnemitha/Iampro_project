# Sampling and Annotation Protocol: Independent Multidisciplinary Holdout Benchmark

**Target System:** CiteGuard Verification Pipeline  
**Protocol Version:** 1.0-Holdout (Frozen)  
**Date:** October 15, 2026  
**Directory:** `datasets/citation_verification/independent_holdout/`  
**Related Paper:** ICDDS 2026 Paper #158 ("CitationGuard: Prompt-Aware Detection and Verification of Hallucinated Citations in Large Language Models")

---

## 1. Rationale and Objective

Peer reviewers noted that the original CiteGuard evaluation (Benchmark V1.0, 600 citations) and its diagnostic update (Benchmark V2.0) were derived from 100 seed papers concentrated in Computer Science and Machine Learning. While Benchmark V2.0 corrected 24 historical no-op mutations, it maintained exact continuity with the original 100 seeds and therefore could not serve as an independent holdout.

The objective of this protocol is to construct a **rigorously independent, multidisciplinary holdout benchmark** of **400 citations** to evaluate CiteGuard's generalization across scholarly disciplines without data leakage, threshold tuning, or seed reuse.

---

## 2. Benchmark Architecture and Stratification

The benchmark comprises exactly **400 citations** structured as follows:

### 2.1 Disciplinary Stratification (100 citations per discipline)
Four broad scholarly disciplines are sampled with equal representation:
1. **Computer Science (`computer_science`):** Cryptography, distributed systems, relational databases, software engineering, and wireless networks (intentionally disjoint from the machine-learning/deep-learning subfields of V1/V2).
2. **Medicine and Biomedical Sciences (`medicine_biomedical`):** Clinical oncology, cardiology, neurology, immunology, pharmacology, and randomized controlled trials.
3. **Natural Sciences (`natural_sciences`):** Astrophysics, condensed matter physics, organic chemistry, climate dynamics, materials science, and geology.
4. **Humanities and Social Sciences (`humanities_social_sciences`):** Econometrics, cognitive psychology, linguistics, sociology, public administration, and economic history.

### 2.2 Class and Error-Type Stratification
- **Genuine Citations (25% / 100 citations):** Ground truth `0` (`error_type: "valid"`), exactly 25 citations per discipline.
- **Perturbed Citations (75% / 300 citations):** Ground truth `1`, balanced across 5 canonical error categories (60 citations per category, exactly 15 per discipline):
  - `corrupted_authors`: 60 citations (15 per discipline)
  - `wrong_venue`: 60 citations (15 per discipline)
  - `wrong_year`: 60 citations (15 per discipline)
  - `doi_mismatch`: 60 citations (15 per discipline)
  - `plausible_fabricated`: 60 citations (15 per discipline)

---

## 3. Seed Selection and Quality Criteria

Genuine seed records were harvested from Crossref using structured API queries targeting high-impact peer-reviewed journal articles.

### 3.1 Inclusion Criteria
To be included as a seed paper, a scholarly record must satisfy all of the following:
1. **Authoritative Registration:** Must possess an active, resolvable Crossref DOI under standard publisher prefixes (`10.1016`, `10.1056`, `10.1103`, `10.1093`, `10.1145`, `10.1109`, etc.).
2. **Metadata Completeness:**
   - Complete article title (minimum 15 characters, at least 3 lexical words).
   - Complete author list with both given and family names.
   - Verified integer publication year between 2000 and 2024.
   - Verifiable journal or conference venue (`container-title`).
3. **Language:** English-language scholarly metadata.

### 3.2 Exclusion Criteria (Negative Filter)
A candidate was immediately rejected and quarantined if:
1. **V1/V2 Seed Overlap:** DOI matches any of the 100 protected seed DOIs in `hard_citation_test_dataset.csv` or `hard_citation_test_dataset_v2.csv`.
2. **Title Overlap:** Normalized title matches any of the 328 distinct citation titles appearing in V1.0 or V2.0 benchmarks.
3. **Incomplete Registry Data:** Author list is empty or venue is missing.

Exactly 100 seed papers (25 per discipline) met all criteria and were preserved in `multidisciplinary_seed_papers.json`.

---

## 4. Controlled Perturbation Rules

Each of the 25 seeds per discipline yields 1 genuine citation and 3 systematically assigned perturbations (75 perturbations per discipline). Across the 25 seeds, error types are assigned cyclically $((i \pmod 5), ((i+1) \pmod 5), ((i+2) \pmod 5))$, guaranteeing that every error category appears exactly 15 times per discipline.

### 4.1 Author Mutation (`corrupted_authors`)
- **Rule:** The first author of the source citation is replaced with the first author from a donor paper within the same discipline.
- **Verification of Change:** Donor search advances cyclically until `normalize_name(donor_first) != normalize_name(source_first)`. The final formatted author string is strictly asserted to differ from the original: `mutated_authors != original_authors`.
- **Ground Truth:** `1` (Hallucinated citation).

### 4.2 Venue Mutation (`wrong_venue`)
- **Rule:** The publication venue is substituted with a donor venue from the same discipline.
- **Verification of Change:** Donor search advances until `donor_venue.lower() != source_venue.lower()`.
- **Ground Truth:** `1` (Hallucinated citation).

### 4.3 Publication Year Mutation (`wrong_year`)
- **Rule:** The publication year is shifted by $\pm 5$ years (even years: $+5$; odd years: $-5$).
- **Verification of Change:** The shifted year is asserted to strictly differ from the source year and remain within 1995–2024. The 5-year displacement avoids borderline preprint/reprint 1-year ambiguities.
- **Ground Truth:** `1` (Hallucinated citation).

### 4.4 DOI Mutation (`doi_mismatch`)
- **Rule:** The DOI is swapped with a valid, distinct donor DOI from the same discipline.
- **Verification of Change:** Source title, authors, year, and venue remain intact, but the DOI points to a completely different publication.
- **Ground Truth:** `1` (Hallucinated citation).

### 4.5 Plausible Fabrication (`plausible_fabricated`)
- **Rule:** A realistic but completely non-existent citation is synthesized for the discipline, combining:
  - A plausible, specialized scholarly title synthesizing modern domain concepts.
  - Realistic academic author names.
  - A reputable journal venue in that field.
  - A non-resolvable synthetic DOI adhering to the standard benchmark prefix `10.9999/citeguard.holdout.<discipline>.<id>`.
- **Verification of Change:** No publication with this title or DOI exists in Crossref, OpenAlex, or Semantic Scholar.
- **Ground Truth:** `1` (Hallucinated citation).

---

## 5. Provenance and Record Schema

Each record in `independent_holdout_dataset.csv` contains 12 explicit fields:

| Field Name | Type | Description |
|---|---|---|
| `id` | Integer | Unique identifier (1 to 400). |
| `discipline` | String | Discipline (`computer_science`, `medicine_biomedical`, `natural_sciences`, `humanities_social_sciences`). |
| `citation` | String | Full formatted citation string. |
| `ground_truth` | Integer | `0` = Valid, `1` = Hallucinated / Error. |
| `error_type` | String | Category (`valid`, `corrupted_authors`, `wrong_venue`, `wrong_year`, `doi_mismatch`, `plausible_fabricated`). |
| `source_doi` | String | Canonical DOI of the seed publication. |
| `donor_doi` | String | DOI of the donor publication (if mutation utilized a donor). |
| `original_field_value` | String | Pre-mutation field value (`""` for valid/fabricated). |
| `mutated_field_value` | String | Post-mutation field value (`""` for valid). |
| `mutation_rule` | String | Explicit name of the mutation rule applied. |
| `retrieval_date` | String | ISO 8601 UTC timestamp of source metadata retrieval. |
| `provenance_source` | String | Data source (`"Crossref"` or `"synthetic_generation"`). |

---

## 6. Pre-Evaluation Validation Checks

Before any evaluation script was executed, `validate_holdout.py` enforced 5 automated quality checks:
1. **Count & Stratification:** Exactly 400 records; 100 valid / 300 perturbed; 100 per discipline; 60 per error category.
2. **Zero Overlap:** Zero matching DOIs, titles, or citation strings between the holdout and V1/V2 benchmarks.
3. **Zero No-Ops:** Every perturbed record verified to have `original_field_value != mutated_field_value`.
4. **Zero Collisions:** All 400 citation strings and IDs verified strictly unique.
5. **Parsing Integrity:** 100% of citations verified parseable by CiteGuard's `extract_citations` and `parse_citation`.

Evaluation proceeded only after all 5 validation checks passed with zero errors.
