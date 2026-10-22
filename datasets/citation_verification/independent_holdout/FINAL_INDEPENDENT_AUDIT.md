# Final Scientific Audit: Independent Holdout Benchmark and Historical Results Reconciliation

**Audit Date:** October 15, 2026  
**Auditor:** Antigravity AI  
**Target Paper:** "CitationGuard: Prompt-Aware Detection and Verification of Hallucinated Citations in Large Language Models" (ICDDS 2026, Paper ID #158)  
**Primary Target Directory:** `datasets/citation_verification/independent_holdout/`  
**Audit Type:** Read-Only Rigorous Verification & Historical Reconciliation  
**Audit Status:** AUDIT COMPLETE — DISCREPANCIES IDENTIFIED & RECONCILED

---

## 1. Files and Scripts Inspected

The following 18 artifacts were inspected and audited directly:

### 1.1 Holdout Benchmark Artifacts (`datasets/citation_verification/independent_holdout/`)
1. [`INDEPENDENT_HOLDOUT_REPORT.md`](file:///c:/Users/A%20S%20Nemitha/Desktop/CiteGuard/datasets/citation_verification/independent_holdout/INDEPENDENT_HOLDOUT_REPORT.md): Scientific report documenting holdout methodology and findings.
2. [`HOLDOUT_AUDIT_REPORT.md`](file:///c:/Users/A%20S%20Nemitha/Desktop/CiteGuard/datasets/citation_verification/independent_holdout/HOLDOUT_AUDIT_REPORT.md): Audit report detailing harvest filtering, counts, and exclusion criteria.
3. [`SAMPLING_AND_ANNOTATION_PROTOCOL.md`](file:///c:/Users/A%20S%20Nemitha/Desktop/CiteGuard/datasets/citation_verification/independent_holdout/SAMPLING_AND_ANNOTATION_PROTOCOL.md): Pre-registered protocol for disciplinary sampling and perturbations.
4. [`holdout_evaluation_config.json`](file:///c:/Users/A%20S%20Nemitha/Desktop/CiteGuard/datasets/citation_verification/independent_holdout/holdout_evaluation_config.json): Frozen configuration and SHA-256 fingerprint registry.
5. [`holdout_results.csv`](file:///c:/Users/A%20S%20Nemitha/Desktop/CiteGuard/datasets/citation_verification/independent_holdout/holdout_results.csv): Summary metric table across the four configurations.
6. [`holdout_detailed_results.csv`](file:///c:/Users/A%20S%20Nemitha/Desktop/CiteGuard/datasets/citation_verification/independent_holdout/holdout_detailed_results.csv): Complete row-level predictions for all 1,600 evaluations (400 citations $\times$ 4 configs).
7. [`holdout_summary.json`](file:///c:/Users/A%20S%20Nemitha/Desktop/CiteGuard/datasets/citation_verification/independent_holdout/holdout_summary.json): Complete machine-readable results including per-discipline and per-error breakdowns.
8. [`independent_holdout_dataset.csv`](file:///c:/Users/A%20S%20Nemitha/Desktop/CiteGuard/datasets/citation_verification/independent_holdout/independent_holdout_dataset.csv): The 400 holdout citations with ground-truth labels and full provenance.
9. [`multidisciplinary_seed_papers.json`](file:///c:/Users/A%20S%20Nemitha/Desktop/CiteGuard/datasets/citation_verification/independent_holdout/multidisciplinary_seed_papers.json): The 100 harvested genuine seed papers from Crossref.
10. [`reproducible_api_cache_holdout.json`](file:///c:/Users/A%20S%20Nemitha/Desktop/CiteGuard/datasets/citation_verification/independent_holdout/reproducible_api_cache_holdout.json): Content-addressed offline cache providing 100% evaluation coverage.
11. [`generate_holdout_dataset.py`](file:///c:/Users/A%20S%20Nemitha/Desktop/CiteGuard/datasets/citation_verification/independent_holdout/generate_holdout_dataset.py): Dataset generation script.
12. [`validate_holdout.py`](file:///c:/Users/A%20S%20Nemitha/Desktop/CiteGuard/datasets/citation_verification/independent_holdout/validate_holdout.py): Pre-evaluation validation suite enforcing disjointness and mutation integrity.
13. [`run_evaluation_holdout.py`](file:///c:/Users/A%20S%20Nemitha/Desktop/CiteGuard/datasets/citation_verification/independent_holdout/run_evaluation_holdout.py): Offline evaluation harness.

### 1.2 Historical V1.0 and V2.0 Artifacts
14. [`targeted_fixes_results.csv`](file:///c:/Users/A%20S%20Nemitha/Desktop/CiteGuard/datasets/citation_verification/targeted_fixes_results.csv): **Authoritative frozen source of truth for accepted paper V1.0 camera-ready results** (dated Aug 17, 2026).
15. [`targeted_fixes_summary.json`](file:///c:/Users/A%20S%20Nemitha/Desktop/CiteGuard/datasets/citation_verification/targeted_fixes_summary.json): Complete archival telemetry for accepted paper V1.0.
16. [`final_results.csv`](file:///c:/Users/A%20S%20Nemitha/Desktop/CiteGuard/datasets/citation_verification/final_results.csv): Results of modern pipeline on V1.0 baseline.
17. [`targeted_fixes_results_v2.csv`](file:///c:/Users/A%20S%20Nemitha/Desktop/CiteGuard/datasets/citation_verification/benchmark_v2/targeted_fixes_results_v2.csv): **Authoritative frozen source of truth for Benchmark V2.0 diagnostic evaluation**.
18. [`REVIEWER_RESPONSE_V2_FINAL.md`](file:///c:/Users/A%20S%20Nemitha/Desktop/CiteGuard/datasets/citation_verification/benchmark_v2/REVIEWER_RESPONSE_V2_FINAL.md): Reviewer response draft documenting the historical vs diagnostic reconciliation.

---

## 2. Independent Recalculation of Holdout Metrics

Every metric was recomputed directly from the 1,600 individual prediction rows in `holdout_detailed_results.csv` using strict mathematical formulas.

### 2.1 Recomputed Confusion Matrices and Metrics
| Configuration | TP | TN | FP | FN | Total | Accuracy | Precision | Recall | Specificity | Balanced Acc | F1-Score | Macro-F1 |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Baseline** | 234 | 94 | 6 | 66 | 400 | 82.00% | 97.50% | 78.00% | 94.00% | 86.00% | 86.67% | **79.49%** |
| **Author Fix** | 279 | 93 | 7 | 21 | 400 | 93.00% | 97.55% | 93.00% | 93.00% | 93.00% | 95.22% | **91.07%** |
| **Venue Fix** | 239 | 94 | 6 | 61 | 400 | 83.25% | 97.55% | 79.67% | 94.00% | 86.83% | 87.71% | **80.72%** |
| **Combined** | 284 | 93 | 7 | 16 | 400 | 94.25% | 97.59% | 94.67% | 93.00% | 93.83% | 96.11% | **92.55%** |

### 2.2 Confidence Intervals Verification (Wilson Score Interval, 95%)
Recomputed using the textbook Wilson score method without continuity correction ($z = 1.959964$):
- **Baseline Accuracy:** $[77.94\%, 85.45\%]$ (Matches `holdout_summary.json`)
- **Combined Accuracy:** $[91.52\%, 96.14\%]$ (Matches `holdout_summary.json`)
- **Combined Precision:** $[95.12\%, 98.83\%]$ (In `holdout_summary.json`: `[95.12, 98.83]`; Report Section 4 text rounded to `[95.09%, 98.84%]`)
- **Combined Recall:** $[91.51\%, 96.69\%]$ (In `holdout_summary.json`: `[91.51, 96.69]`; Report Section 4 text rounded to `[91.47%, 96.72%]`)
- **Combined Specificity:** $[86.25\%, 96.57\%]$ (In `holdout_summary.json`: `[86.25, 96.57]`; Report Section 4 text rounded to `[86.26%, 96.59%]`)

### 2.3 Reconciliation of Disciplinary Counts to Aggregate
For the primary **Combined configuration**:
- **Computer Science:** $\text{TP}=70, \text{TN}=22, \text{FP}=3, \text{FN}=5$ (Total = 100)
- **Medicine / Biomedical:** $\text{TP}=71, \text{TN}=25, \text{FP}=0, \text{FN}=4$ (Total = 100)
- **Natural Sciences:** $\text{TP}=71, \text{TN}=24, \text{FP}=1, \text{FN}=4$ (Total = 100)
- **Humanities / Social Sciences:** $\text{TP}=72, \text{TN}=22, \text{FP}=3, \text{FN}=3$ (Total = 100)
- **Reconciled Sums:**
  $$\sum \text{TP} = 70 + 71 + 71 + 72 = \mathbf{284}$$
  $$\sum \text{TN} = 22 + 25 + 24 + 22 = \mathbf{93}$$
  $$\sum \text{FP} = 3 + 0 + 1 + 3 = \mathbf{7}$$
  $$\sum \text{FN} = 5 + 4 + 4 + 3 = \mathbf{16}$$
  $$\text{Total} = 284 + 93 + 7 + 16 = \mathbf{400}$$
The discipline-level counts reconcile with aggregate counts without any discrepancy.

### 2.4 Error-Category Reconciliation
- `valid`: 93 / 100 correct (93.00% Specificity)
- `corrupted_authors`: 50 / 60 detected (83.33% Recall)
- `wrong_venue`: 54 / 60 detected (90.00% Recall)
- `wrong_year`: 60 / 60 detected (100.00% Recall)
- `doi_mismatch`: 60 / 60 detected (100.00% Recall)
- `plausible_fabricated`: 60 / 60 detected (100.00% Recall)
- **False Negative Sum:** $(60 - 50) + (60 - 54) + 0 + 0 + 0 = 10 + 6 = \mathbf{16\text{ FN}}$. Matches aggregate $\text{FN} = 16$.

### 2.5 Identified Minor Discrepancies in `INDEPENDENT_HOLDOUT_REPORT.md`
1. **Macro-F1 Precision:** The summary CSV and JSON record Macro-F1 as **92.55%** for Combined (and **79.49%** for Baseline), whereas `INDEPENDENT_HOLDOUT_REPORT.md` wrote **92.51%** (and **79.52%**). The difference arises from calculating Macro-F1 from unrounded floating-point class F1s vs rounded components.
2. **Confidence Interval Minor Rounding:** The reported Precision and Recall CIs in Section 4 text differed by $< 0.04\%$ from the exact values in `holdout_summary.json`. The JSON artifact is the authoritative source.

---

## 3. Disjointness and Provenance Audit

### 3.1 Overlap Verification
The holdout dataset was programmatically checked against all 100 V1/V2 seeds and 328 historical titles:
- **Canonical DOI Overlap:** **0** (160 unique holdout DOIs vs 100 V1/V2 DOIs).
- **Normalized Title Overlap:** **0** (160 unique holdout titles vs 328 V1/V2 titles).
- **Citation String Overlap:** **0** (400 holdout citations vs 1,139 historical strings).
- **Provenance Coverage:** Every record contains populated `source_doi`, `retrieval_date`, and `provenance_source`. For perturbed records, `original_field_value`, `mutated_field_value`, `mutation_rule`, and `donor_doi` (where applicable) are fully documented.

### 3.2 Mutation Effectiveness (Zero No-Ops)
Across all 300 perturbed records, `mutated_field_value != original_field_value` was asserted and verified. Zero no-op perturbations exist in the dataset.

---

## 4. Ground-Truth Limitations and Rigorous Characterization

To prevent scientific overclaiming in reviewer correspondence:

1. **Programmatic Synthetic Perturbation vs Naturally Occurring Hallucinations:**
   - The holdout perturbations were generated programmatically using controlled substitution rules (donor author swapping, donor venue swapping, $\pm 5$ year shifts, donor DOI swapping).
   - These represent **controlled synthetic stress tests**, not naturally occurring, conversational hallucinations sampled from uncontrolled LLM generations.
2. **Programmatic Disjointness vs Human Annotation:**
   - The disjointness was verified programmatically through exact canonical string, DOI, and title normalization.
   - Ground-truth labels reflect deterministic generation provenance, **not double-blind manual human annotation**.
3. **Synthetic Fabricated DOIs:**
   - The 60 plausible fabricated citations use realistic journal titles and synthesized article titles, paired with synthetic non-resolvable DOIs (`10.9999/citeguard.holdout...`). In real-world LLM hallucinations, models sometimes hallucinate real DOIs pointing to unrelated papers (which CiteGuard evaluates via the `doi_mismatch` category).

---

## 5. Historical V1/V2 Reconciliation: Root Cause of Table Discrepancy

### 5.1 The Discrepancy Identified in `INDEPENDENT_HOLDOUT_REPORT.md`
In Section 7 of `INDEPENDENT_HOLDOUT_REPORT.md`, the diagnostic comparison table erroneously stated:
- *Accepted Paper (V1.0) Combined F1:* **97.0%** (ERROR)
- *Accepted Paper (V1.0) Baseline Recall:* **73.0%** (ERROR)
- *Accepted Paper (V1.0) Combined Recall:* **95.2%** (ERROR)
- *Diagnostic V2.0 Combined F1:* **97.6%** (ERROR)

### 5.2 Authoritative Source of Truth from Frozen Artifacts
We audited the original, frozen historical artifacts:
- [`datasets/citation_verification/targeted_fixes_results.csv`](file:///c:/Users/A%20S%20Nemitha/Desktop/CiteGuard/datasets/citation_verification/targeted_fixes_results.csv) (Archival freeze, Aug 17, 2026):
  - **Current CiteGuard (Baseline):** $\text{TP}=403, \text{TN}=75, \text{FP}=25, \text{FN}=97$
    - $\text{Accuracy} = \mathbf{79.67\%}$ | $\text{Recall} = \mathbf{80.60\%}$ | $\text{Precision} = \mathbf{94.16\%}$ | $\text{F1} = \mathbf{86.85\%}$
  - **Combined (Author + Venue Fix):** $\text{TP}=467, \text{TN}=75, \text{FP}=25, \text{FN}=33$
    - $\text{Accuracy} = \mathbf{90.33\%}$ | $\text{Recall} = \mathbf{93.40\%}$ | $\text{Precision} = \mathbf{94.92\%}$ | $\mathbf{F1 = 94.15\%}$
- [`datasets/citation_verification/benchmark_v2/targeted_fixes_results_v2.csv`](file:///c:/Users/A%20S%20Nemitha/Desktop/CiteGuard/datasets/citation_verification/benchmark_v2/targeted_fixes_results_v2.csv) (Benchmark V2.0 Diagnostic):
  - **Current CiteGuard (Baseline):** $\text{TP}=350, \text{TN}=93, \text{FP}=7, \text{FN}=150$
    - $\text{Accuracy} = \mathbf{73.83\%}$ | $\text{Recall} = \mathbf{70.00\%}$ | $\text{Precision} = \mathbf{98.04\%}$ | $\text{F1} = \mathbf{81.68\%}$
  - **Combined (Author + Venue Fix):** $\text{TP}=474, \text{TN}=93, \text{FP}=7, \text{FN}=26$
    - $\text{Accuracy} = \mathbf{94.50\%}$ | $\text{Recall} = \mathbf{94.80\%}$ | $\text{Precision} = \mathbf{98.54\%}$ | $\mathbf{F1 = 96.64\%}$

### 5.3 Authoritative Reconciled Cross-Benchmark Comparison Table
The four distinct evaluation phases must be presented using their verified historical numbers:

| Evaluation Phase / Dataset | Seeds / Provenance | N | TP | TN | FP | FN | Accuracy | F1 Score | Recall | Specificity |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **1. Accepted Paper Camera-Ready (V1.0)** | 100 CS/ML Seeds (Archival Aug 17, 2026) | 600 | 467 | 75 | 25 | 33 | **90.33%** | **94.15%** | **93.40%** | **75.00%** |
| **2. Modern Pipeline on V1.0 Benchmark** | 100 CS/ML Seeds (Commit d6893ba) | 600 | 452 | 93 | 7 | 48 | **90.83%** | **94.26%** | **90.40%** | **93.00%** |
| **3. Diagnostic Benchmark V2.0** | 100 CS/ML Seeds (Repaired 24 No-Ops) | 600 | 474 | 93 | 7 | 26 | **94.50%** | **96.64%** | **94.80%** | **93.00%** |
| **4. Independent Multidisciplinary Holdout** | **100 Multidisciplinary Seeds (Disjoint)** | **400** | **284** | **93** | **7** | **16** | **94.25%** | **96.11%** | **94.67%** | **93.00%** |

---

## 6. Reproducibility Assessment

- **Reproducibility of Holdout Metrics:** **CONFIRMED 100% REPRODUCIBLE.**
  - Executing `python datasets/citation_verification/independent_holdout/run_evaluation_holdout.py` runs in **~9.2 seconds** and regenerates the exact TP, TN, FP, FN, Accuracy (94.25%), F1 (96.11%), Recall (94.67%), and Specificity (93.00%).
- **Offline Cache Integrity:** Confirmed. Zero live network calls are made during evaluation. All 400 entries are served deterministically from `reproducible_api_cache_holdout.json`.
- **Threshold Integrity:** Production code and thresholds (`title_threshold = 80.0`, `author_threshold = 70.0`, `venue_threshold = 70.0`) remain unaltered.

---

## 7. Legitimate Scope of Generalization Claim

The holdout benchmark supports the following specific scientific claim:
> *"When evaluated on an independent holdout dataset of 400 citations across four distinct academic disciplines (Computer Science, Medicine/Biomedical, Natural Sciences, Humanities/Social Sciences) derived from 100 non-overlapping seed papers, CiteGuard's Combined configuration demonstrated robust cross-disciplinary generalization, achieving 94.25% accuracy (95% CI: [91.52%, 96.14%]) and 96.11% F1-score without any discipline-specific parameter tuning."*

### Limitations to Disclose
1. Does not prove generalization to unindexed non-English literature or predatory journals without Crossref indexing.
2. Evaluates controlled synthetic perturbations rather than open-domain human-prompted conversational hallucinations.
3. Does not replace the accepted camera-ready conference paper results.

---

## 8. Required Document Corrections

Before final submission of reviewer correspondence, the following corrections should be applied:

### In `datasets/citation_verification/independent_holdout/INDEPENDENT_HOLDOUT_REPORT.md`:
1. **Replace Table in Section 7:** Replace the erroneous V1 Combined F1 of 97.0% and V2 Combined F1 of 97.6% with the verified archival numbers from Section 5.3 above (V1: Accuracy 90.33%, F1 94.15%; V2: Accuracy 94.50%, F1 96.64%).
2. **Align Macro-F1 Precision:** Standardize Macro-F1 to **92.55%** (matching `holdout_results.csv` and `holdout_summary.json`).
3. **Align Confidence Interval Text:** Standardize text in Section 4 to match the exact values in `holdout_summary.json` (Precision CI: [95.12%, 98.83%]; Recall CI: [91.51%, 96.69%]; Specificity CI: [86.25%, 96.57%]).

### In `datasets/citation_verification/benchmark_v2/REVIEWER_RESPONSE_V2_FINAL.md`:
1. If the independent holdout is incorporated into the reviewer response, it must be introduced as an **additional four-tier progression row** (`4. Independent Multidisciplinary Holdout`) without overwriting the historical archival baseline (90.33% accuracy, 94.15% F1) or the clean-label diagnostic V2.0 (94.50% accuracy, 96.64% F1).
2. Clearly describe the holdout as a **controlled, programmatically disjoint synthetic benchmark across four disciplines**, avoiding unverified claims of "human double-blind evaluation."

---

## 9. Summary of Audit Checklist

| Item | Requirement | Audit Verdict | Notes |
|---|---|:---:|---|
| **1** | Full Inspection of Artifacts | **PASSED** | 18 files audited across holdout, V1, and V2 directories. |
| **2** | Metric Recomputation from Raw Data | **PASSED** | Recomputed all 1,600 rows; TP=284, TN=93, FP=7, FN=16 verified. |
| **3** | Disjointness from V1/V2 | **PASSED** | 0 overlapping DOIs, 0 titles, 0 citation strings. |
| **4** | Ground-Truth Traceability | **PASSED** | 100% of 400 citations have complete provenance and non-zero mutation. |
| **5** | Historical Reconciliation | **RECONCILED** | Discrepancy (97.0% vs 94.15%) identified and reconciled to frozen archival V1. |
| **6** | Reproducibility | **PASSED** | 100% reproducible offline in 9.2 seconds. |
| **7** | Generalization Scope | **VERIFIED** | Formulated precise, defensible cross-disciplinary claim with explicit limits. |
| **8** | Document Corrections Identified | **COMPLETED** | Actionable text adjustments detailed for holdout report and reviewer draft. |
| **9** | Safety Rules Enforced | **PASSED** | Read-only audit; zero Git operations; zero production or benchmark overwrites. |

---

*This concludes the independent scientific audit.*
