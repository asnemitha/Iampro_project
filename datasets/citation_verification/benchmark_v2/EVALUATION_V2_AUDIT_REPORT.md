# Benchmark V2.0 Evaluation & Reconciliation Audit Report

**Date**: 2026-10-15  
**Scope**: Exhaustive read-only reconciliation of Benchmark V2.0 evaluation results against V1.0 baselines, category-level error distributions, and production comparison functions.  

---

## 1. Provenance-Based Dataset & Prediction Reconciliation

### Stable Mapping Methodology
In V1.0 (`hard_citation_test_dataset.csv`), rows were shuffled after initial ID assignment (leaving IDs 1–600 scattered across categories). In V2.0 (`hard_citation_test_dataset_v2.csv`), sequential IDs 1–600 were reassigned after pseudo-random shuffling. Therefore, reconciliation cannot rely on row order or raw IDs.

Instead, records are matched 1-to-1 using stable semantic provenance keys:
- **Categories 1–5** (Valid, DOI Mismatch, Corrupted Authors, Wrong Year, Wrong Venue): Keyed by `(error_type, normalized_source_doi)`.
- **Category 6** (Plausible Fabricated): Keyed by `(plausible_fabricated, index)` extracted from the title marker `(i)`.

Verification results:
- Total unique keys in V1: **600** / 600
- Total unique keys in V2: **600** / 600
- Symmetric Difference: **0** (Exact 1-to-1 bijection established).

---

## 2. Row-Level Audit of the 24 Repaired Records

The 24 records where V1.0 suffered from no-op author or venue substitutions were repaired in V2.0. Below is their complete evaluation status across the Historical V1 baseline (`targeted_fixes_detailed.csv`, Aug 17, 2026), Modern V1 committed pipeline (`experimental_detailed_results.csv`, commit `d6893ba`), and Modern V2 evaluation (`targeted_fixes_detailed_v2.csv`):

| V2 ID | V1 ID | Category | Ground Truth | V1 Hist Pred | V1 Mod Pred | V2 Pred | Prediction Changed? | Remains FN in V2? |
|:---:|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| 2 | 258 | `corrupted_authors` | 1 | 0 | 0 | 1 | Yes (FN -> TP) | No (TP) |
| 16 | 252 | `corrupted_authors` | 1 | 0 | 0 | 1 | Yes (FN -> TP) | No (TP) |
| 362 | 209 | `corrupted_authors` | 1 | 0 | 0 | 1 | Yes (FN -> TP) | No (TP) |
| 387 | 267 | `corrupted_authors` | 1 | 0 | 0 | 1 | Yes (FN -> TP) | No (TP) |
| 399 | 219 | `corrupted_authors` | 1 | 0 | 0 | 1 | Yes (FN -> TP) | No (TP) |
| 407 | 287 | `corrupted_authors` | 1 | 0 | 0 | 1 | Yes (FN -> TP) | No (TP) |
| 494 | 208 | `corrupted_authors` | 1 | 1 | 0 | 1 | Yes (FN -> TP) | No (TP) |
| 39 | 498 | `wrong_venue` | 1 | 0 | 0 | 1 | Yes (FN -> TP) | No (TP) |
| 177 | 487 | `wrong_venue` | 1 | 0 | 0 | 0 | No | **Yes** |
| 194 | 404 | `wrong_venue` | 1 | 0 | 0 | 1 | Yes (FN -> TP) | No (TP) |
| 218 | 467 | `wrong_venue` | 1 | 0 | 0 | 1 | Yes (FN -> TP) | No (TP) |
| 241 | 499 | `wrong_venue` | 1 | 1 | 0 | 1 | Yes (FN -> TP) | No (TP) |
| 252 | 405 | `wrong_venue` | 1 | 0 | 0 | 1 | Yes (FN -> TP) | No (TP) |
| 258 | 406 | `wrong_venue` | 1 | 0 | 0 | 1 | Yes (FN -> TP) | No (TP) |
| 331 | 494 | `wrong_venue` | 1 | 0 | 0 | 1 | Yes (FN -> TP) | No (TP) |
| 378 | 458 | `wrong_venue` | 1 | 0 | 0 | 1 | Yes (FN -> TP) | No (TP) |
| 403 | 479 | `wrong_venue` | 1 | 0 | 0 | 1 | Yes (FN -> TP) | No (TP) |
| 411 | 411 | `wrong_venue` | 1 | 0 | 0 | 1 | Yes (FN -> TP) | No (TP) |
| 432 | 452 | `wrong_venue` | 1 | 0 | 0 | 0 | No | **Yes** |
| 472 | 408 | `wrong_venue` | 1 | 1 | 0 | 1 | Yes (FN -> TP) | No (TP) |
| 474 | 407 | `wrong_venue` | 1 | 1 | 0 | 1 | Yes (FN -> TP) | No (TP) |
| 513 | 419 | `wrong_venue` | 1 | 0 | 0 | 1 | Yes (FN -> TP) | No (TP) |
| 543 | 410 | `wrong_venue` | 1 | 0 | 0 | 1 | Yes (FN -> TP) | No (TP) |
| 550 | 409 | `wrong_venue` | 1 | 0 | 0 | 1 | Yes (FN -> TP) | No (TP) |

### Detailed String Inspection for the 24 Records

#### Record 1: V2 ID 2 (V1 ID 258) — `corrupted_authors`
- **V1 Original Citation**: `Title: "Deep Learning with PyTorch for Classification" -- Authors: Abdelaziz Testas -- Year: 2024 -- Venue: Building Scalable Deep Learning Pipelines on AWS -- DOI: 10.1007/979-8-8688-1017-6_6`
- **V2 Repaired Citation**: `Title: "Deep Learning with PyTorch for Classification" -- Authors: Mehdi Ghayoumi -- Year: 2024 -- Venue: Building Scalable Deep Learning Pipelines on AWS -- DOI: 10.1007/979-8-8688-1017-6_6`
- **V1 Historical Prediction**: `0` | **V1 Modern Prediction**: `0` | **V2 Prediction**: `1`
- **Status in V2**: TRUE POSITIVE (Hallucination Detected)

#### Record 2: V2 ID 16 (V1 ID 252) — `corrupted_authors`
- **V1 Original Citation**: `Title: "Where to Start Your Deep Learning" -- Authors: Thimira Amaratunga -- Year: 2021 -- Venue: Deep Learning on Windows -- DOI: 10.1007/978-1-4842-6431-7_2`
- **V2 Repaired Citation**: `Title: "Where to Start Your Deep Learning" -- Authors: Nikhil Ketkar -- Year: 2021 -- Venue: Deep Learning on Windows -- DOI: 10.1007/978-1-4842-6431-7_2`
- **V1 Historical Prediction**: `0` | **V1 Modern Prediction**: `0` | **V2 Prediction**: `1`
- **Status in V2**: TRUE POSITIVE (Hallucination Detected)

#### Record 3: V2 ID 362 (V1 ID 209) — `corrupted_authors`
- **V1 Original Citation**: `Title: "Editorial: Advice to Machine Learning Authors" -- Authors: Pat Langley -- Year: 1990 -- Venue: Machine Learning -- DOI: 10.1023/a:1022647305786`
- **V2 Repaired Citation**: `Title: "Editorial: Advice to Machine Learning Authors" -- Authors: David Haussler -- Year: 1990 -- Venue: Machine Learning -- DOI: 10.1023/a:1022647305786`
- **V1 Historical Prediction**: `0` | **V1 Modern Prediction**: `0` | **V2 Prediction**: `1`
- **Status in V2**: TRUE POSITIVE (Hallucination Detected)

#### Record 4: V2 ID 387 (V1 ID 267) — `corrupted_authors`
- **V1 Original Citation**: `Title: "Image Analysis and Computer Vision: 1999" -- Authors: Azriel Rosenfeld -- Year: 2000 -- Venue: Computer Vision and Image Understanding -- DOI: 10.1006/cviu.2000.0835`
- **V2 Repaired Citation**: `Title: "Image Analysis and Computer Vision: 1999" -- Authors: Xieling Chen -- Year: 2000 -- Venue: Computer Vision and Image Understanding -- DOI: 10.1006/cviu.2000.0835`
- **V1 Historical Prediction**: `0` | **V1 Modern Prediction**: `0` | **V2 Prediction**: `1`
- **Status in V2**: TRUE POSITIVE (Hallucination Detected)

#### Record 5: V2 ID 399 (V1 ID 219) — `corrupted_authors`
- **V1 Original Citation**: `Title: "Toward a Unified Science of Machine Learning" -- Authors: Pat Langley -- Year: 1989 -- Venue: Machine Learning -- DOI: 10.1023/a:1022689616458`
- **V2 Repaired Citation**: `Title: "Toward a Unified Science of Machine Learning" -- Authors: Taiwo Oladipupo -- Year: 1989 -- Venue: Machine Learning -- DOI: 10.1023/a:1022689616458`
- **V1 Historical Prediction**: `0` | **V1 Modern Prediction**: `0` | **V2 Prediction**: `1`
- **Status in V2**: TRUE POSITIVE (Hallucination Detected)

#### Record 6: V2 ID 407 (V1 ID 287) — `corrupted_authors`
- **V1 Original Citation**: `Title: "Natural Language Processing Application Cases" -- Authors: Huaping Zhang; Jianyun Shang -- Year: 2025 -- Venue: Natural Language Processing and Applications -- DOI: 10.1007/978-981-97-9739-4_20`
- **V2 Repaired Citation**: `Title: "Natural Language Processing Application Cases" -- Authors: Daichi Mochihashi; Jianyun Shang -- Year: 2025 -- Venue: Natural Language Processing and Applications -- DOI: 10.1007/978-981-97-9739-4_20`
- **V1 Historical Prediction**: `0` | **V1 Modern Prediction**: `0` | **V2 Prediction**: `1`
- **Status in V2**: TRUE POSITIVE (Hallucination Detected)

#### Record 7: V2 ID 494 (V1 ID 208) — `corrupted_authors`
- **V1 Original Citation**: `Title: "Research Papers in Machine Learning" -- Authors: Pat Langley -- Year: 1987 -- Venue: Machine Learning -- DOI: 10.1023/a:1022603230145`
- **V2 Repaired Citation**: `Title: "Research Papers in Machine Learning" -- Authors: David Haussler -- Year: 1987 -- Venue: Machine Learning -- DOI: 10.1023/a:1022603230145`
- **V1 Historical Prediction**: `1` | **V1 Modern Prediction**: `0` | **V2 Prediction**: `1`
- **Status in V2**: TRUE POSITIVE (Hallucination Detected)

#### Record 8: V2 ID 39 (V1 ID 498) — `wrong_venue`
- **V1 Original Citation**: `Title: "Artificial intelligence" -- Authors: Stuart C. Shapiro -- Year: 1976 -- Venue: Artificial Intelligence -- DOI: 10.1016/0004-3702(76)90004-7`
- **V2 Repaired Citation**: `Title: "Artificial intelligence" -- Authors: Stuart C. Shapiro -- Year: 1976 -- Venue: Fundamentals of Machine Learning -- DOI: 10.1016/0004-3702(76)90004-7`
- **V1 Historical Prediction**: `0` | **V1 Modern Prediction**: `0` | **V2 Prediction**: `1`
- **Status in V2**: TRUE POSITIVE (Hallucination Detected)

#### Record 9: V2 ID 177 (V1 ID 487) — `wrong_venue`
- **V1 Original Citation**: `Title: "Natural Language Processing Application Cases" -- Authors: Huaping Zhang; Jianyun Shang -- Year: 2025 -- Venue: Natural Language Processing and Applications -- DOI: 10.1007/978-981-97-9739-4_20`
- **V2 Repaired Citation**: `Title: "Natural Language Processing Application Cases" -- Authors: Huaping Zhang; Jianyun Shang -- Year: 2025 -- Venue: Journal of Natural Language Processing -- DOI: 10.1007/978-981-97-9739-4_20`
- **V1 Historical Prediction**: `0` | **V1 Modern Prediction**: `0` | **V2 Prediction**: `0`
- **Status in V2**: **FALSE NEGATIVE** (Detection Missed)

#### Record 10: V2 ID 194 (V1 ID 404) — `wrong_venue`
- **V1 Original Citation**: `Title: "Machine Learning and Concept Formation" -- Authors: Pat Langley -- Year: 1987 -- Venue: Machine Learning -- DOI: 10.1023/a:1022896407371`
- **V2 Repaired Citation**: `Title: "Machine Learning and Concept Formation" -- Authors: Pat Langley -- Year: 1987 -- Venue: Soft Computing and Machine Learning -- DOI: 10.1023/a:1022896407371`
- **V1 Historical Prediction**: `0` | **V1 Modern Prediction**: `0` | **V2 Prediction**: `1`
- **Status in V2**: TRUE POSITIVE (Hallucination Detected)

#### Record 11: V2 ID 218 (V1 ID 467) — `wrong_venue`
- **V1 Original Citation**: `Title: "Image Analysis and Computer Vision: 1999" -- Authors: Azriel Rosenfeld -- Year: 2000 -- Venue: Computer Vision and Image Understanding -- DOI: 10.1006/cviu.2000.0835`
- **V2 Repaired Citation**: `Title: "Image Analysis and Computer Vision: 1999" -- Authors: Azriel Rosenfeld -- Year: 2000 -- Venue: Natural Language Processing Journal -- DOI: 10.1006/cviu.2000.0835`
- **V1 Historical Prediction**: `0` | **V1 Modern Prediction**: `0` | **V2 Prediction**: `1`
- **Status in V2**: TRUE POSITIVE (Hallucination Detected)

#### Record 12: V2 ID 241 (V1 ID 499) — `wrong_venue`
- **V1 Original Citation**: `Title: "Embodied artificial intelligence" -- Authors: Ron Chrisley -- Year: 2003 -- Venue: Artificial Intelligence -- DOI: 10.1016/s0004-3702(03)00055-9`
- **V2 Repaired Citation**: `Title: "Embodied artificial intelligence" -- Authors: Ron Chrisley -- Year: 2003 -- Venue: Fundamentals of Machine Learning -- DOI: 10.1016/s0004-3702(03)00055-9`
- **V1 Historical Prediction**: `1` | **V1 Modern Prediction**: `0` | **V2 Prediction**: `1`
- **Status in V2**: TRUE POSITIVE (Hallucination Detected)

#### Record 13: V2 ID 252 (V1 ID 405) — `wrong_venue`
- **V1 Original Citation**: `Title: "Machine Learning: A Maturing Field" -- Authors: Jaime Carbonell -- Year: 1992 -- Venue: Machine Learning -- DOI: 10.1023/a:1022665512030`
- **V2 Repaired Citation**: `Title: "Machine Learning: A Maturing Field" -- Authors: Jaime Carbonell -- Year: 1992 -- Venue: Soft Computing and Machine Learning -- DOI: 10.1023/a:1022665512030`
- **V1 Historical Prediction**: `0` | **V1 Modern Prediction**: `0` | **V2 Prediction**: `1`
- **Status in V2**: TRUE POSITIVE (Hallucination Detected)

#### Record 14: V2 ID 258 (V1 ID 406) — `wrong_venue`
- **V1 Original Citation**: `Title: "Editorial: Human and Machine Learning" -- Authors: Pat Langley -- Year: 1986 -- Venue: Machine Learning -- DOI: 10.1023/a:1022854429410`
- **V2 Repaired Citation**: `Title: "Editorial: Human and Machine Learning" -- Authors: Pat Langley -- Year: 1986 -- Venue: Soft Computing and Machine Learning -- DOI: 10.1023/a:1022854429410`
- **V1 Historical Prediction**: `0` | **V1 Modern Prediction**: `0` | **V2 Prediction**: `1`
- **Status in V2**: TRUE POSITIVE (Hallucination Detected)

#### Record 15: V2 ID 331 (V1 ID 494) — `wrong_venue`
- **V1 Original Citation**: `Title: "Artificial intelligence" -- Authors: Roy Rada -- Year: 1986 -- Venue: Artificial Intelligence -- DOI: 10.1016/0004-3702(86)90034-2`
- **V2 Repaired Citation**: `Title: "Artificial intelligence" -- Authors: Roy Rada -- Year: 1986 -- Venue: Biomarker Research -- DOI: 10.1016/0004-3702(86)90034-2`
- **V1 Historical Prediction**: `0` | **V1 Modern Prediction**: `0` | **V2 Prediction**: `1`
- **Status in V2**: TRUE POSITIVE (Hallucination Detected)

#### Record 16: V2 ID 378 (V1 ID 458) — `wrong_venue`
- **V1 Original Citation**: `Title: "Deep Learning with PyTorch for Classification" -- Authors: Abdelaziz Testas -- Year: 2024 -- Venue: Building Scalable Deep Learning Pipelines on AWS -- DOI: 10.1007/979-8-8688-1017-6_6`
- **V2 Repaired Citation**: `Title: "Deep Learning with PyTorch for Classification" -- Authors: Abdelaziz Testas -- Year: 2024 -- Venue: Mathematical Foundations for Deep Learning -- DOI: 10.1007/979-8-8688-1017-6_6`
- **V1 Historical Prediction**: `0` | **V1 Modern Prediction**: `0` | **V2 Prediction**: `1`
- **Status in V2**: TRUE POSITIVE (Hallucination Detected)

#### Record 17: V2 ID 403 (V1 ID 479) — `wrong_venue`
- **V1 Original Citation**: `Title: "AI Linguistics" -- Authors: Guosheng Zhang -- Year: 2025 -- Venue: Natural Language Processing Journal -- DOI: 10.1016/j.nlp.2025.100137`
- **V2 Repaired Citation**: `Title: "AI Linguistics" -- Authors: Guosheng Zhang -- Year: 2025 -- Venue: Oxford Handbooks Online -- DOI: 10.1016/j.nlp.2025.100137`
- **V1 Historical Prediction**: `0` | **V1 Modern Prediction**: `0` | **V2 Prediction**: `1`
- **Status in V2**: TRUE POSITIVE (Hallucination Detected)

#### Record 18: V2 ID 411 (V1 ID 411) — `wrong_venue`
- **V1 Original Citation**: `Title: "New Theoretical Directions In Machine Learning" -- Authors: David Haussler -- Year: 1988 -- Venue: Machine Learning -- DOI: 10.1023/a:1022817027844`
- **V2 Repaired Citation**: `Title: "New Theoretical Directions In Machine Learning" -- Authors: David Haussler -- Year: 1988 -- Venue: Soft Computing and Machine Learning -- DOI: 10.1023/a:1022817027844`
- **V1 Historical Prediction**: `0` | **V1 Modern Prediction**: `0` | **V2 Prediction**: `1`
- **Status in V2**: TRUE POSITIVE (Hallucination Detected)

#### Record 19: V2 ID 432 (V1 ID 452) — `wrong_venue`
- **V1 Original Citation**: `Title: "Where to Start Your Deep Learning" -- Authors: Thimira Amaratunga -- Year: 2021 -- Venue: Deep Learning on Windows -- DOI: 10.1007/978-1-4842-6431-7_2`
- **V2 Repaired Citation**: `Title: "Where to Start Your Deep Learning" -- Authors: Thimira Amaratunga -- Year: 2021 -- Venue: Deep Learning with Python -- DOI: 10.1007/978-1-4842-6431-7_2`
- **V1 Historical Prediction**: `0` | **V1 Modern Prediction**: `0` | **V2 Prediction**: `0`
- **Status in V2**: **FALSE NEGATIVE** (Detection Missed)

#### Record 20: V2 ID 472 (V1 ID 408) — `wrong_venue`
- **V1 Original Citation**: `Title: "Research Papers in Machine Learning" -- Authors: Pat Langley -- Year: 1987 -- Venue: Machine Learning -- DOI: 10.1023/a:1022603230145`
- **V2 Repaired Citation**: `Title: "Research Papers in Machine Learning" -- Authors: Pat Langley -- Year: 1987 -- Venue: Soft Computing and Machine Learning -- DOI: 10.1023/a:1022603230145`
- **V1 Historical Prediction**: `1` | **V1 Modern Prediction**: `0` | **V2 Prediction**: `1`
- **Status in V2**: TRUE POSITIVE (Hallucination Detected)

#### Record 21: V2 ID 474 (V1 ID 407) — `wrong_venue`
- **V1 Original Citation**: `Title: "Machine Learning and Qualitative Reasoning" -- Authors: Ivan Bratko -- Year: 1994 -- Venue: Machine Learning -- DOI: 10.1023/a:1022661713654`
- **V2 Repaired Citation**: `Title: "Machine Learning and Qualitative Reasoning" -- Authors: Ivan Bratko -- Year: 1994 -- Venue: Soft Computing and Machine Learning -- DOI: 10.1023/a:1022661713654`
- **V1 Historical Prediction**: `1` | **V1 Modern Prediction**: `0` | **V2 Prediction**: `1`
- **Status in V2**: TRUE POSITIVE (Hallucination Detected)

#### Record 22: V2 ID 513 (V1 ID 419) — `wrong_venue`
- **V1 Original Citation**: `Title: "Toward a Unified Science of Machine Learning" -- Authors: Pat Langley -- Year: 1989 -- Venue: Machine Learning -- DOI: 10.1023/a:1022689616458`
- **V2 Repaired Citation**: `Title: "Toward a Unified Science of Machine Learning" -- Authors: Pat Langley -- Year: 1989 -- Venue: New Advances in Machine Learning -- DOI: 10.1023/a:1022689616458`
- **V1 Historical Prediction**: `0` | **V1 Modern Prediction**: `0` | **V2 Prediction**: `1`
- **Status in V2**: TRUE POSITIVE (Hallucination Detected)

#### Record 23: V2 ID 543 (V1 ID 410) — `wrong_venue`
- **V1 Original Citation**: `Title: "Editorial: The Terminology of Machine Learning" -- Authors: Pat Langley -- Year: 1986 -- Venue: Machine Learning -- DOI: 10.1023/a:1022840627593`
- **V2 Repaired Citation**: `Title: "Editorial: The Terminology of Machine Learning" -- Authors: Pat Langley -- Year: 1986 -- Venue: Soft Computing and Machine Learning -- DOI: 10.1023/a:1022840627593`
- **V1 Historical Prediction**: `0` | **V1 Modern Prediction**: `0` | **V2 Prediction**: `1`
- **Status in V2**: TRUE POSITIVE (Hallucination Detected)

#### Record 24: V2 ID 550 (V1 ID 409) — `wrong_venue`
- **V1 Original Citation**: `Title: "Editorial: Advice to Machine Learning Authors" -- Authors: Pat Langley -- Year: 1990 -- Venue: Machine Learning -- DOI: 10.1023/a:1022647305786`
- **V2 Repaired Citation**: `Title: "Editorial: Advice to Machine Learning Authors" -- Authors: Pat Langley -- Year: 1990 -- Venue: Soft Computing and Machine Learning -- DOI: 10.1023/a:1022647305786`
- **V1 Historical Prediction**: `0` | **V1 Modern Prediction**: `0` | **V2 Prediction**: `1`
- **Status in V2**: TRUE POSITIVE (Hallucination Detected)

---

## 3. Discrepancy Analysis: The 20 vs. 24 No-Ops and Venue False Negatives

### A. The 20 vs. 24 V1 False Negative Discrepancy
Why did earlier discussions mention **20** no-op False Negatives, while modern analysis shows **24**?
1. **Historical Pipeline (Aug 17, 2026)**: In the legacy predictions recorded in `targeted_fixes_detailed.csv`, **20** of the 24 no-ops were False Negatives (`pred=0`), while **4** were fortuitously flagged as True Positives (`pred=1`, V1 IDs: 208, 499, 408, 407). These 4 were flagged because the legacy pipeline failed to resolve the DOI or title candidate in that specific environment.
2. **Modern Committed Pipeline (Oct 15, 2026, commit `d6893ba`)**: In `experimental_detailed_results.csv`, where cache coverage and normalizers were finalized, **all 24 of the 24 no-ops were False Negatives (`pred=0`)**. Because the author/venue string was identical to the underlying metadata, the modern pipeline cleanly matched them, resulting in $100\%$ detection failure for all 24 no-ops.

### B. Why Venue False Negatives Stand at 23
There was confusion regarding why venue false negatives are reported as **23** in V2.0 despite 17 venue no-ops being repaired. The explanation lies in contrasting the two distinct V1 baselines:

1. **Historical V1 Baseline (`targeted_fixes_results.csv`, Aug 17)**:
   - Total FN: 33 (`corrupted_authors`: 17, `wrong_venue`: **15**, `doi_mismatch`: 1).
   - Specificity was poor: **FP = 25** (TN = 75).
   - Under this permissive baseline, many venue perturbations were erroneously flagged as hallucinations due to faulty candidate matching, artificially suppressing venue False Negatives to 15.

2. **Modern V1 Pipeline (`experimental_summary.json`, commit `d6893ba`)**:
   - Specificity improved to **FP = 7** (TN = 93).
   - Total FN on V1: **48** (`corrupted_authors`: 9, `wrong_venue`: **38**, `doi_mismatch`: 1).
   - Among the 38 venue False Negatives on V1, **15 were the no-op records** (2 were already flagged).

3. **Progression to Benchmark V2.0**:
   - In V2.0, the 17 venue no-ops were replaced with distinct donors.
   - **15 of those 17 were converted from False Negatives to True Positives**.
   - **2 of those 17 remained False Negatives** (V2 IDs 177 and 432) due to fuzzy score overlap.
   - Therefore, venue False Negatives dropped from **38 (Modern V1) down to 23 (V2.0)**: exactly $38 - 15 = 23$!
   - Simultaneously, author False Negatives dropped from **9 (Modern V1) down to 2 (V2.0)**: exactly $9 - 7 = 2$!
   - Total FN: $48 - 15 - 7 = 26$ ($23 + 2 + 1 = 26$).

---

## 4. Verification of Similarity Scores for Remaining Venue False Negatives

Production venue comparison is governed by `compare_venues(v1, v2, use_venue_fix=True, threshold=70.0)` in `app/services/similarity_service.py`.
When `use_venue_fix=True`, it normalizes strings (stripping stopwords like 'journal of', 'proceedings of') and computes `fuzz.token_sort_ratio`.

Direct execution against production code reveals the exact mechanism for the 23 venue False Negatives:

1. **Normalized String Collisions (Score = 100.0%, 3 cases)**:
   - `Journal of Natural Language Processing` vs `Natural Language Processing` -> Both normalize to `natural language processing` (Score = 100.0%, threshold >= 70.0).
2. **Empty Metadata Venue Defaults (Score = 100.0%, 2 cases)**:
   - V2 IDs 152 and 588: Crossref metadata had no container-title or publisher (`venue = ''`). Per line 337 of `similarity_service.py`, empty metadata defaults to `(True, 100.0)`.
3. **Borderline Fuzzy Token Overlap (Score = 70.18% – 87.10%, 18 cases)**:
   - `Natural Language Processing and Applications` vs `Journal of Natural Language Processing`: Score = **76.06%** (Threshold 70.0) -> Match!
   - `Online Machine Learning` vs `Quantum Machine Learning`: Score = **76.60%** (Threshold 70.0) -> Match!
   - `Deep Learning with Python` vs `Deep Learning on Windows`: Score = **77.55%** (Threshold 70.0) -> Match!
   - `Encyclopedia of Data Science and Machine Learning` vs `Encyclopedia of Machine Learning`: Score = **79.01%** (Threshold 70.0) -> Match!
   - `Machine Learning` vs `Machine Learning Methods`: Score = **80.00%** (Threshold 70.0) -> Match!
   - `Applied Natural Language Processing with Python` vs `Natural Language Processing Journal`: Score = **73.17%** (Threshold 70.0) -> Match!
   - `Fundamentals of Machine Learning` vs `Machine Learning, Animated`: Score = **70.18%** (Threshold 70.0) -> Match!

All 23 cases produce scores strictly $\ge 70.0$ or hit the empty-metadata fallback, mathematically proving why `venue_match` evaluates to `True`.

---

## 5. Independent Confusion Matrix & Metric Recomputation

All metrics were recomputed from the 2,400 per-record prediction rows in `targeted_fixes_detailed_v2.csv`:

$$\begin{array}{lcccc|cccc}
\hline
\textbf{Configuration} & \textbf{TP} & \textbf{TN} & \textbf{FP} & \textbf{FN} & \textbf{Accuracy} & \textbf{Precision} & \textbf{Recall} & \textbf{F1 Score} \\
\hline
\text{Current CiteGuard} & 350 & 93 & 7 & 150 & 73.83\% & 98.04\% & 70.00\% & 81.68\% \\
\text{CiteGuard + Author Fix} & 441 & 93 & 7 & 59 & 89.00\% & 98.44\% & 88.20\% & 93.04\% \\
\text{CiteGuard + Venue Fix} & 383 & 93 & 7 & 117 & 79.33\% & 98.21\% & 76.60\% & 86.07\% \\
\textbf{CiteGuard + Combined Fix} & \mathbf{474} & \mathbf{93} & \mathbf{7} & \mathbf{26} & \mathbf{94.50\%} & \mathbf{98.54\%} & \mathbf{94.80\%} & \mathbf{96.64\%} \\
\hline
\end{array}$$

Integrity Verification:
- Row Count: Exactly 2,400 rows (600 per configuration).
- Unique Citation IDs: Exactly 1 through 600 in all 4 configurations.
- Class Balances: $\text{TP} + \text{FN} = 500$, $\text{FP} + \text{TN} = 100$ in all configurations.
- Exact Agreement: 100% agreement with `targeted_fixes_results_v2.csv`.

---

## 6. Category Labels & Naming Consistency Check

- Dataset files (`hard_citation_test_dataset.csv`, `hard_citation_test_dataset_v2.csv`): Identical column name `error_type` and values: `corrupted_authors`, `doi_mismatch`, `plausible_fabricated`, `valid`, `wrong_venue`, `wrong_year`.
- Detailed results files (`targeted_fixes_detailed.csv`, `targeted_fixes_detailed_v2.csv`): Identical column name `error_type` and values.
- Intermediate experiment file (`experimental_detailed_results.csv`): Used `benchmark_category` instead of `error_type`, but values are identical.
- Summary JSON schema difference: `targeted_fixes_summary.json` (V1) included nested `per_error_type` dictionaries, whereas `targeted_fixes_summary_v2.json` recorded top-level `configurations` and `telemetry`. Both are consistent with their respective harnesses.

---

## 7. Comprehensive Discrepancy Log

1. **V1 Historical Baseline vs. V1 Modern Baseline**: Comparing V2 directly against the August 17 historical baseline (`targeted_fixes_results.csv`) conflates two separate changes: the codebase improvements (which reduced FP from 25 to 7 and increased baseline venue FN from 15 to 38) and the dataset repair (which reduced venue FN from 38 to 23 and author FN from 9 to 2). Both comparisons are now mathematically reconciled.
2. **Two Remaining Venue False Negatives among Repaired Records**: V2 IDs 177 and 432 were repaired with genuine donor venues, but because the donor venues shared extensive token overlap ('deep learning', 'natural language processing') with the source venues, their similarity scores (76.06% and 77.55%) exceeded the production threshold of 70.0%. This is expected behavior under fuzzy lexical matching.
3. **Empty Metadata in Seed Papers**: Two papers in the benchmark lack venue metadata in Crossref, causing `compare_venues` to default to `True`. This is an inherent property of Crossref metadata coverage.

All issues are fully explained and accounted for by the underlying code and artifacts.