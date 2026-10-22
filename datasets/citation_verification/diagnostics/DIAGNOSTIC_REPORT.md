# CitationGuard: Citation-Level Reproducibility Audit & Diagnostic Report

**Project:** CitationGuard: Prompt-Aware Detection and Verification of Hallucinated Citations in Large Language Models  
**Conference:** IEEE ICDDS 2026 (Paper ID: 158)  
**Investigation Type:** Citation-Level Discrepancy & Matching Logic Audit  
**Artifact Directory:** `datasets/citation_verification/diagnostics/`  

---

## 1. Executive Summary & Verification Status

This audit investigated the mathematical and behavioral discrepancy between:
1. **The Accepted ICDDS 2026 Camera-Ready Paper Results** (preserved in `targeted_fixes_detailed.csv`, `targeted_fixes_results.csv`, `final_results_corrected.csv`, and `final_summary.json`).
2. **The Offline Reproducible Evaluation Script** (`run_reproducible_evaluation.py`) running against `reproducible_api_cache.json`.

### Key Findings:
- **Label Mapping & Metrics:** Both scripts share identical label definitions ($1 = \text{Hallucinated}$, $0 = \text{Valid/Accurate}$) and mathematically consistent formulas for TP, FP, TN, FN, Accuracy, Precision, Recall, and F1.
- **Saved Paper Results Integrity:** The 2,400 per-citation predictions in `targeted_fixes_detailed.csv` match the published paper metrics across all 4 configurations with **100% bit-for-bit precision**.
- **Source of Divergence:** The discrepancy between the preserved paper numbers and running today's offline script is driven by **three confirmed architectural evolutions in the pipeline between August 17, 2026 and September 20, 2026**, combined with an evaluation harness argument mismatch.
- **Venue Fix Invariance:** In the modern codebase, Configuration 1 (Current CiteGuard) and Configuration 3 (CiteGuard + Venue Fix) produce identical confusion matrices ($TP=343, FP=7, TN=93, FN=157$) because `fuzz.token_set_ratio >= 70` evaluates to 100% on word subsets, rendering the `use_venue_fix` substring toggle completely inert.
- **Scientific Reproducibility Status:** The preserved paper results are mathematically authentic and verifiable from repo artifacts. However, an **independent live rerun** yielding identical numbers is not possible without using the frozen matching rules and non-expiring cache state under which the original experiments were executed.

---

## 2. Audit of Formulas, Label Mappings, and Artifact Agreement (Goals 1, 2, & 7)

### A. Label Mappings
Across `hard_citation_test_dataset.csv`, `targeted_fixes_detailed.csv`, `reproduce_icdds2026_benchmark.py`, and `run_reproducible_evaluation.py`:
- `ground_truth = 1`: The citation contains a fabricated element (hallucinated).
- `ground_truth = 0`: The citation is authentic and verifiable (valid).
- `prediction = 1`: System flags citation as hallucinated (`citation_accurate = False`).
- `prediction = 0`: System verifies citation as accurate (`citation_accurate = True`).

### B. Metric Definitions
- $\text{TP}$: $\text{ground\_truth} = 1$ and $\text{prediction} = 1$ (Hallucination correctly flagged).
- $\text{TN}$: $\text{ground\_truth} = 0$ and $\text{prediction} = 0$ (Valid citation verified).
- $\text{FP}$: $\text{ground\_truth} = 0$ and $\text{prediction} = 1$ (Valid citation falsely flagged as hallucination).
- $\text{FN}$: $\text{ground\_truth} = 1$ and $\text{prediction} = 0$ (Hallucination missed; falsely claimed accurate).
- $\text{Accuracy} = \frac{\text{TP} + \text{TN}}{\text{Total}}$
- $\text{Precision} = \frac{\text{TP}}{\text{TP} + \text{FP}}$
- $\text{Recall} = \frac{\text{TP}}{\text{TP} + \text{FN}}$
- $\text{F1} = \frac{2 \cdot \text{Precision} \cdot \text{Recall}}{\text{Precision} + \text{Recall}}$

### C. Cross-Artifact Agreement (Table I & Summary Artifacts)
Recalculating metrics directly from the 2,400 rows of `targeted_fixes_detailed.csv` confirms exact alignment with `targeted_fixes_results.csv`, `targeted_fixes_summary.json`, and `final_results_corrected.csv`:

| Configuration | Total | TP | FP | TN | FN | Accuracy | Precision | Recall | F1-Score | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Current CiteGuard** | 600 | 403 | 25 | 75 | 97 | 79.67% | 94.16% | 80.60% | 86.85% | **VERIFIED MATCH** |
| **CiteGuard + Author Fix** | 600 | 461 | 25 | 75 | 39 | 89.33% | 94.86% | 92.20% | 93.51% | **VERIFIED MATCH** |
| **CiteGuard + Venue Fix** | 600 | 409 | 25 | 75 | 91 | 80.67% | 94.24% | 81.80% | 87.58% | **VERIFIED MATCH** |
| **CiteGuard + Author + Venue Fix** | 600 | 467 | 25 | 75 | 33 | 90.33% | 94.92% | 93.40% | 94.15% | **VERIFIED MATCH** |

---

## 3. Citation-Level Comparison: Saved vs. Current Predictions (Goals 3 & 4)

We generated [`prediction_changes.csv`](file:///c:/Users/A%20S%20Nemitha/Desktop/CiteGuard/datasets/citation_verification/diagnostics/prediction_changes.csv) containing all 2,400 comparisons (600 citations $\times$ 4 configurations) keyed by stable `citation_id`.

### Prediction Change Counts by Configuration:
- **Current CiteGuard (Baseline):** **78 changed predictions**
  - `valid`: 18 changed ($1 \to 0$, FP reduced to TN — improvement)
  - `wrong_venue`: 42 changed ($1 \to 0$, TP dropped to FN)
  - `corrupted_authors`: 18 changed ($1 \to 0$, TP dropped to FN)
- **CiteGuard + Author Fix:** **70 changed predictions**
  - `valid`: 18 changed ($1 \to 0$)
  - `wrong_venue`: 42 changed ($1 \to 0$)
  - `corrupted_authors`: 10 changed ($1 \to 0$)
- **CiteGuard + Venue Fix:** **84 changed predictions**
  - `valid`: 18 changed ($1 \to 0$)
  - `wrong_venue`: 48 changed ($1 \to 0$)
  - `corrupted_authors`: 18 changed ($1 \to 0$)
- **CiteGuard + Author + Venue Fix:** **76 changed predictions**
  - `valid`: 18 changed ($1 \to 0$)
  - `wrong_venue`: 48 changed ($1 \to 0$)
  - `corrupted_authors`: 10 changed ($1 \to 0$)

### Citation-Level Evidence & Case Studies:

#### Case 1: Valid Citations (CID 35, 30, 54, 20)
- **Citation (CID 35):** Thimira Amaratunga, "What Is Deep Learning?", *Deep Learning on Windows*, 2021, DOI: `10.1007/978-1-4842-6431-7_1`
- **Saved Paper Prediction:** 1 (Flagged as Hallucination — False Positive)
- **Current Prediction:** 0 (Verified as Accurate — True Negative)
- **Verified Root Cause:** In the August 2026 pipeline, CrossRef title querying returned candidate papers with low title overlap (`"Deep learning? What deep learning?"`), failing candidate retrieval. When DOI fallback injection (`candidates.append(doi_paper)`) was added in September 2026, the authoritative DOI record was retained, correctly validating the citation.

#### Case 2: Mutated Venue (CID 424, 460, 466, 474)
- **Citation (CID 460):** Claimed Venue: `"Deep Learning"`, Actual Venue: `"Mathematical Foundations for Deep Learning"`
- **Saved Paper Prediction:** 1 (Flagged as Hallucination — True Positive in Venue Fix)
- **Current Prediction:** 0 (Missed Hallucination — False Negative in both Baseline and Venue Fix)
- **Scores:** `token_set_ratio = 100.0`, `token_sort_ratio = 47.3`
- **Verified Root Cause:** In `similarity_service.py`, `token_set_ratio` calculates the token intersection. Because `"deep learning"` is a subset of `"mathematical foundations for deep learning"`, `token_set_ratio` evaluates to 100%. Even when `use_venue_fix=True` skips the substring check, `token_set_ratio >= 70` fires immediately after, returning `match = True`.

#### Case 3: Corrupted Authors (CID 275, 222, 214, 230)
- **Citation (CID 275):** Claimed Author: `"Tayyaba Hussain"`, Actual Author: `"Raymond Lee"`, DOI: `10.1007/978-981-96-3208-4_1`
- **Saved Baseline Prediction:** 1 (Flagged as Hallucination)
- **Current Baseline Prediction:** 0 (Missed Hallucination)
- **Verified Root Cause:** In the original baseline, candidate retrieval by title failed to find the paper, flagging it by "Paper Not Found". In the modern pipeline, DOI fallback finds the paper. However, because Baseline sets `use_author_fix=False`, line 408 forces `author_check = True`. Since title, year, venue, and DOI match, Baseline declares the citation accurate despite 0% author similarity.

---

## 4. Root Cause Analysis: Why Venue Fix Equals Baseline in Current Code (Goal 5)

Tracing code execution in `backend/app/services/` revealed two specific implementation flaws:

1. **Short-Circuit in `similarity_service.py` (`compare_venues`):**
   ```python
   # Substring containment (allowed in baseline, removed when use_venue_fix=True)
   if not use_venue_fix:
       if (len(n1) >= 3 and n1 in n2) or (len(n2) >= 3 and n2 in n1):
           return True, 95.0

   # Token set ratio handles word subsets
   score = fuzz.token_set_ratio(n1, n2)
   if score >= 70:
       return True, float(score)
   ```
   When `use_venue_fix=True`, the script skips line 368. However, because every substring containment example also constitutes a word subset, line 372 evaluates `fuzz.token_set_ratio` to 100.0, which satisfies `score >= 70`. Both branches return `match = True`.

2. **Parameter Dropping in `candidate_ranker.py`:**
   In `candidate_ranker.py`, `rank_candidates(..., use_venue_fix=False)` receives `use_venue_fix`, but at line 100 it calls:
   ```python
   venue_match, venue_sim = compare_venues(
       parsed_metadata.get("venue"),
       candidate.get("venue")
   )
   ```
   It omits `use_venue_fix=use_venue_fix`, defaulting to `False` regardless of caller configuration.

---

## 5. Non-Production Diagnostic Test Execution (Goals 6 & 9)

A dedicated diagnostic test suite was created and executed:
[`test_venue_and_metadata_matching.py`](file:///c:/Users/A%20S%20Nemitha/Desktop/CiteGuard/datasets/citation_verification/diagnostics/test_venue_and_metadata_matching.py)

### Execution Command:
```powershell
python datasets/citation_verification/diagnostics/test_venue_and_metadata_matching.py
```

### Actual Output:
```
....
----------------------------------------------------------------------
Ran 4 tests in 0.002s

OK
```

### What These Tests Proved:
- **Test 1 (Subset Venue Matching):** Proved that `"Deep Learning"` vs `"Mathematical Foundations for Deep Learning"` yields `token_set_ratio = 100.0` and matches under both Baseline and Venue Fix.
- **Test 2 (Venue Aliases):** Proved that `VENUE_ALIASES` successfully maps acronyms like `"NeurIPS"` and `"ICML"` to their full scholarly titles.
- **Test 3 (Author Corruption):** Proved that corrupted author lists (`"Tayyaba Hussain"` vs `"Raymond Lee"`) score 0.0% author similarity and are only caught when `use_author_fix=True`.
- **Test 4 (DOI Matching):** Proved that URL-prefixed, uppercase, and bare DOIs are correctly normalized, while mismatched DOIs are strictly rejected.

---

## 6. Synthesis: Confirmed Findings, Unresolved Questions, & Recommendations

### Confirmed Findings:
1. **The Accepted ICDDS 2026 Paper Results are Genuine:** The exact numbers published in the paper are present in repo prediction logs and summary JSON files. There was no fabrication of metrics.
2. **Current Pipeline is Substantially Better on Real-World Valid Citations:** False positives on valid papers dropped from 25% down to 7% (TN rose from 75 to 93), increasing precision from 94.16% to 98.00%.
3. **Current Pipeline is Less Strict on Substring Venue Mutations:** Because `token_set_ratio` was introduced post-freeze to tolerate messy user prompts, it allows mutated venues with common subset words to pass verification.
4. **Harness Defect Repaired:** The `*args, **kwargs` addition to `run_reproducible_evaluation.py` resolved the 188 silent `TypeError` crashes.

### Unresolved Questions:
1. Did the authors freeze a specific git commit hash corresponding to the August 17 submission that had the strict venue substring logic? (Commit `daaa6a7` appears to be the candidate).
2. Should future benchmark evaluations use a frozen benchmark matching profile rather than executing live production code that changes over time?

### Proposed Recommendations:
1. **Preserve Current Production Rules for Web/API:** The live application benefits from high precision (98.00%) and tolerance of valid user citations.
2. **Keep Separate Benchmark Verification:** Maintain `reproduce_icdds2026_benchmark.py` in the repository as the official reviewer reproducibility script for ICDDS 2026 Table I and Table II.
3. **If Venue Fix is to be Reactivated in Modern Code:** When `use_venue_fix=True`, `compare_venues` should use `fuzz.token_sort_ratio` rather than `token_set_ratio`, ensuring that subset venue expansions (e.g. `"Deep Learning"` vs `"Mathematical Foundations for Deep Learning"`) are caught.
