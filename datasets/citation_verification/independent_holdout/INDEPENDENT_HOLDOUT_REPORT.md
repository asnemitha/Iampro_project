# CiteGuard Independent Multidisciplinary Holdout Benchmark: Evaluation and Scientific Report

**Authors:** CiteGuard Research Team  
**Date:** October 15, 2026  
**Target Paper:** "CitationGuard: Prompt-Aware Detection and Verification of Hallucinated Citations in Large Language Models" (ICDDS 2026, Paper ID #158)  
**Location:** `datasets/citation_verification/independent_holdout/`  
**Dataset Artifact:** `independent_holdout_dataset.csv` (SHA-256: `08df6cff595ed576e38ea508c6b6463782702c1527d96af085cdad708bfe7aee`)

---

## 1. Executive Summary & Reviewer Alignment

In review feedback for ICDDS 2026 Paper #158, reviewers raised two related concerns:
1. **Dataset Scale and Disciplinary Diversity:** The published benchmark comprised 600 citations derived exclusively from 100 Computer Science and Machine Learning seed papers.
2. **Evaluation Independence:** Benchmark V2.0 corrected 24 historical no-op mutations, but because it reused the exact 100 CS seeds from V1.0, it served as a diagnostic repair rather than an independent holdout.

To directly address these concerns with full scientific rigor, we designed, generated, validated, and evaluated an **Independent Multidisciplinary Holdout Benchmark** of **400 citations**.

### Key Scientific Findings
1. **Zero Data Leakage:** The holdout benchmark shares **zero seed papers, zero DOIs, zero paper titles, and zero citation strings** with V1.0 or V2.0 (100% disjointness verified).
2. **Cross-Disciplinary Generalization:** CiteGuard's Combined configuration demonstrated robust, uniform performance across all four disciplines without any discipline-specific tuning:
   - **Computer Science:** 92.00% Accuracy | 94.59% F1 | 93.33% Recall | 88.00% Specificity
   - **Medicine & Biomedical Sciences:** 96.00% Accuracy | 97.26% F1 | 94.67% Recall | 100.00% Specificity
   - **Natural Sciences:** 95.00% Accuracy | 96.60% F1 | 94.67% Recall | 96.00% Specificity
   - **Humanities & Social Sciences:** 94.00% Accuracy | 96.00% F1 | 96.00% Recall | 88.00% Specificity
3. **Macro Performance:** Across the full 400-citation holdout, CiteGuard Combined achieved:
   - **Accuracy:** **94.25%** (95% CI: [91.52%, 96.14%])
   - **F1-Score:** **96.11%** (Macro-F1: **92.55%**)
   - **Recall (Sensitivity):** **94.67%** (95% CI: [91.51%, 96.69%])
   - **Specificity:** **93.00%** (95% CI: [86.25%, 96.57%])
   - **Precision:** **97.59%** (95% CI: [95.12%, 98.83%])
4. **Reduction of Author & Venue Vulnerabilities:** Author Fix reduced false negatives from 66 to 21 (a 68.2% reduction), and the Combined configuration brought false negatives down to 16 (a 75.8% reduction), confirming that the targeted algorithmic fixes generalize beyond computer science to medicine, natural sciences, and social sciences.

---

## 2. Benchmark Design & Stratification

The benchmark was created following a pre-registered sampling protocol (`SAMPLING_AND_ANNOTATION_PROTOCOL.md`) with explicit constraints:
- **Total Citations:** 400
- **Genuine Citations (`ground_truth = 0`):** 100 (25.0%)
- **Perturbed Citations (`ground_truth = 1`):** 300 (75.0%)
- **Disciplinary Representation:** Exactly 100 citations per discipline (25 genuine + 75 perturbed).
- **Error Category Representation:** Exactly 60 citations per error category (15 per discipline).

### Benchmark Composition Matrix
| Discipline | Valid (GT=0) | Corrupted Authors | Wrong Venue | Wrong Year | DOI Mismatch | Plausible Fabricated | Total |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Computer Science** | 25 | 15 | 15 | 15 | 15 | 15 | **100** |
| **Medicine / Biomedical** | 25 | 15 | 15 | 15 | 15 | 15 | **100** |
| **Natural Sciences** | 25 | 15 | 15 | 15 | 15 | 15 | **100** |
| **Humanities / Social Sciences** | 25 | 15 | 15 | 15 | 15 | 15 | **100** |
| **Total** | **100** | **60** | **60** | **60** | **60** | **60** | **400** |

---

## 3. Disjointness and Leakage Prevention

To ensure strict independence, candidate seed papers harvested from Crossref were filtered against all existing repository records:
- `hard_citation_test_dataset.csv` (V1.0)
- `hard_citation_test_dataset_v2.csv` (V2.0)
- `citation_test_dataset.csv` (Initial V1.0)

### Audit Verification (`validate_holdout.py`)
```text
Protected V1/V2 DOIs   : 100
Holdout DOIs           : 160 (100 genuine seed + 60 synthetic)
DOI Overlap Count      : 0 (100% Disjoint)

Protected V1/V2 Titles : 328
Holdout Titles         : 160 (100 genuine seed + 60 synthetic)
Title Overlap Count    : 0 (100% Disjoint)

Citation Overlap Count : 0 (100% Disjoint)
Zero No-Op Mutations   : Verified across all 300 perturbed records (100% distinct)
Parsing Integrity      : 400 / 400 successfully parsed by extract_citations and parse_citation
```

---

## 4. Empirical Evaluation Results

The evaluation was executed using the content-addressed offline harness `run_evaluation_holdout.py` against `reproducible_api_cache_holdout.json`. All production thresholds (`title_threshold = 80.0`, `author_threshold = 70.0`, `venue_threshold = 70.0`) remained strictly unaltered.

### Overall Performance Summary (N = 400)
| Metric | Baseline | Author Fix | Venue Fix | Combined (Author + Venue) |
|---|:---:|:---:|:---:|:---:|
| **True Positives (TP)** | 234 | 279 | 239 | **284** |
| **True Negatives (TN)** | 94 | 93 | 94 | **93** |
| **False Positives (FP)** | 6 | 7 | 6 | **7** |
| **False Negatives (FN)** | 66 | 21 | 61 | **16** |
| **Accuracy** | 82.00% | 93.00% | 83.25% | **94.25%** |
| *Accuracy 95% CI* | [77.94%, 85.45%] | [90.07%, 95.11%] | [79.28%, 86.59%] | **[91.52%, 96.14%]** |
| **Precision** | 97.50% | 97.55% | 97.55% | **97.59%** |
| *Precision 95% CI* | [94.65%, 98.85%] | [94.98%, 98.83%] | [94.74%, 98.88%] | **[95.12%, 98.83%]** |
| **Recall (Sensitivity)** | 78.00% | 93.00% | 79.67% | **94.67%** |
| *Recall 95% CI* | [72.97%, 82.32%] | [89.55%, 95.35%] | [74.79%, 83.84%] | **[91.51%, 96.69%]** |
| **Specificity** | 94.00% | 93.00% | 94.00% | **93.00%** |
| *Specificity 95% CI* | [87.52%, 97.22%] | [86.25%, 96.57%] | [87.52%, 97.22%] | **[86.25%, 96.57%]** |
| **Balanced Accuracy** | 86.00% | 93.00% | 86.83% | **93.83%** |
| **F1-Score** | 86.67% | 95.22% | 87.71% | **96.11%** |
| **Macro-F1** | 79.49% | 91.07% | 80.72% | **92.55%** |

---

## 5. Disciplinary Breakdown (Combined Configuration)

To verify cross-domain robustness, metrics were computed independently across all four disciplines (100 citations per discipline):

| Discipline | TP | TN | FP | FN | Accuracy | F1-Score | Recall | Specificity |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Computer Science** | 70 | 22 | 3 | 5 | **92.00%** | **94.59%** | 93.33% | 88.00% |
| **Medicine / Biomedical** | 71 | 25 | 0 | 4 | **96.00%** | **97.26%** | 94.67% | 100.00% |
| **Natural Sciences** | 71 | 24 | 1 | 4 | **95.00%** | **96.60%** | 94.67% | 96.00% |
| **Humanities / Social Sciences** | 72 | 22 | 3 | 3 | **94.00%** | **96.00%** | 96.00% | 88.00% |

### Key Observations by Discipline
1. **Medicine / Biomedical achieved the highest accuracy (96.00%) and specificity (100.00%):** Clinical journals (e.g. *New England Journal of Medicine*, *The Lancet*, *JAMA*) feature highly standardized metadata in Crossref, allowing DOI and author verification to operate with near-zero noise.
2. **Natural Sciences achieved 95.00% accuracy and 96.60% F1:** Physical and chemical society publications (*Physical Review Letters*, *JACS*) exhibited strong metadata stability.
3. **Computer Science (92.00%) and HSS (94.00%):** CS and HSS venues frequently employ non-standard journal abbreviations or diverse author-name formatting (e.g., single initials vs. full middle names), resulting in 3 false positives each, while maintaining high recall ($\ge 93.3\%$).

---

## 6. Error Category Breakdown & False Negative Analysis

| Error Category | Ground Truth | Baseline Detected | Combined Detected | Baseline Recall | Combined Recall |
|---|:---:|:---:|:---:|:---:|:---:|
| `valid` | 100 | 94 / 100 | 93 / 100 | 94.00% (Spec) | 93.00% (Spec) |
| `corrupted_authors` | 60 | 5 / 60 | **50 / 60** | 8.33% | **83.33%** |
| `wrong_venue` | 60 | 49 / 60 | **54 / 60** | 81.67% | **90.00%** |
| `wrong_year` | 60 | 60 / 60 | **60 / 60** | 100.00% | **100.00%** |
| `doi_mismatch` | 60 | 60 / 60 | **60 / 60** | 100.00% | **100.00%** |
| `plausible_fabricated` | 60 | 60 / 60 | **60 / 60** | 100.00% | **100.00%** |

### Root Cause of the Remaining 16 False Negatives
In the Combined configuration, only 16 false negatives remain out of 300 perturbed citations:
1. **10 Author False Negatives:**
   - In 10 citations with 4+ authors, replacing the first author with a donor author reduced the author token set overlap to ~72–75%, which remains slightly above the conservative 70.0% author similarity threshold.
   - *Design rationale:* Preserving threshold = 70.0 prevents false rejections on multi-author consortia where author ordering varies across registries.
2. **6 Venue False Negatives:**
   - In 6 cases, the donor venue shared common parent keywords (e.g., "Transactions", "Journal", "Studies") with the source venue, resulting in Levenshtein / token sort similarity $\ge 70.0\%$.
   - *Design rationale:* Tightening venue similarity below 70.0 would severely penalize valid venue abbreviations (e.g., *Proc. Natl. Acad. Sci.* vs. *Proceedings of the National Academy of Sciences*).

---

## 7. Diagnostic Comparison: V1.0 vs. V2.0 vs. Independent Holdout

> [!NOTE]
> The table below presents a **separate diagnostic comparison** across benchmarks. Benchmark V1.0 contains the accepted paper's camera-ready results; Benchmark V2.0 is the controlled diagnostic evaluation on corrected seeds; the Independent Holdout is an independent, non-overlapping cross-disciplinary evaluation.

| Evaluation Phase / Dataset | Seeds / Provenance | N | TP | TN | FP | FN | Accuracy | F1 Score | Recall | Specificity |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **1. Accepted Paper Camera-Ready (V1.0)** | 100 CS/ML Seeds (Archival Aug 17, 2026) | 600 | 467 | 75 | 25 | 33 | **90.33%** | **94.15%** | **93.40%** | **75.00%** |
| **2. Modern Pipeline on V1.0 Benchmark** | 100 CS/ML Seeds (Commit `d6893ba`) | 600 | 452 | 93 | 7 | 48 | **90.83%** | **94.26%** | **90.40%** | **93.00%** |
| **3. Diagnostic Benchmark V2.0** | 100 CS/ML Seeds (Repaired 24 No-Ops) | 600 | 474 | 93 | 7 | 26 | **94.50%** | **96.64%** | **94.80%** | **93.00%** |
| **4. Independent Multidisciplinary Holdout** | **100 Multidisciplinary Seeds (Disjoint)** | **400** | **284** | **93** | **7** | **16** | **94.25%** | **96.11%** | **94.67%** | **93.00%** |

### Scientific Significance of the Comparison
1. **Stability Across Disciplines:** CiteGuard's Combined configuration achieves **94.25% Accuracy** and **96.11% F1** on the independent holdout, demonstrating strong generalization relative to the accepted paper's archival camera-ready baseline (90.33% accuracy, 94.15% F1) and the clean-label diagnostic V2.0 (94.50% accuracy, 96.64% F1).
2. **Consistent Author Fix Impact:** Across all evaluated benchmarks, Author Fix is the primary driver of hallucination detection, boosting baseline recall substantially (from 80.60% to 93.40% in V1.0 archival; from 70.00% to 94.80% in V2.0; and from 78.00% to 94.67% in the holdout).
3. **High Specificity Preserved:** Modern pipeline specificity is maintained at **93.00%** on both V2.0 and the holdout (up from 75.00% in V1.0 archival camera-ready due to subsequent candidate ranking and normalizer improvements), confirming that CiteGuard does not inflate hallucination recall at the expense of falsely rejecting genuine research.

---

## 8. Reproducibility & Integrity Confirmations

1. **Frozen Artifact Checksums:**
   - `independent_holdout_dataset.csv`: `08df6cff595ed576e38ea508c6b6463782702c1527d96af085cdad708bfe7aee`
   - `reproducible_api_cache_holdout.json`: `023b9bcb2e6eb642719b8954ed6000146be0b2473d29f3881f0d7dbae5b3178d`
   - `holdout_evaluation_config.json`: `FROZEN`
2. **Zero Modification to Production Code:**
   - Production backend similarity functions, rankers, and thresholds (`70.0%`) were completely unchanged.
3. **Zero Modification to Historical Artifacts:**
   - V1.0 and V2.0 CSVs, caches, figures, and manuscripts remain byte-for-byte identical.
4. **Zero Git Operations:**
   - No Git commits, pushes, merges, or branch modifications were performed.

---

## 9. Reproduction Commands

To independently validate and reproduce the holdout benchmark evaluation:

```bash
# 1. Run the rigorous 5-check validation suite (asserts 100% disjointness, zero no-ops, exact counts)
python datasets/citation_verification/independent_holdout/validate_holdout.py

# 2. Run the offline evaluation harness across all 4 configurations
python datasets/citation_verification/independent_holdout/run_evaluation_holdout.py
```
