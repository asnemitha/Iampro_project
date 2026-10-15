# CitationGuard: Comprehensive Final Validation Report (v3)

**Branch:** `experiment/venue-fix` (Isolated Git branch; unmerged)  
**Experiment & Validation Directory:** `datasets/citation_verification/experiments_venue_fix/validation/`  
**Dataset:** 600 benchmark instances (`hard_citation_test_dataset.csv`) evaluated against `reproducible_api_cache.json`  
**Status:** **Read-Only Audit Completed — Raw Artifacts Reconciled — Production `main` Untouched Pending Explicit Approval.**

---

## 1. Item 1: Recalculation of Threshold Score Distributions & Resolution of Discrepancies

### A. Resolution of the CID 460 Score Discrepancy:
In `FINAL_VALIDATION_REPORT_V2.md`, CID 460 was erroneously referenced inside the text bullet for the $[60, 70)$ band as:
> `"- Scores in [60, 70): 16 instances (e.g., CID 424 at 64.0, CID 460 at 47.3)."`

A recalculation directly from the raw metadata and similarity service resolves this error:
- **Citation ID:** `460` (`wrong_venue`, Ground Truth: `1`, Hallucinated)
- **Claimed Venue:** `"Deep Learning"` $\to$ normalized: `"deep learning"`
- **Matched Authoritative Venue:** `"Mathematical Foundations for Deep Learning"` $\to$ normalized: `"mathematical foundations for deep learning"`
- **Similarity Computation:**
  - Token sort ratio on normalized venue strings:
    $$\text{fuzz.token\_sort\_ratio}(\text{"deep learning"}, \text{"mathematical foundations for deep learning"}) = 47.27$$
  - `compare_venues()` output: `(False, 47.2727)`
- **Discrepancy Resolution:**
  A score of **47.27** falls strictly into the **$< 60$ score band** ($[40, 50)$). It does **not** reside within $[60, 70)$. Because $47.27 < 60$, CID 460 is correctly rejected as a venue mismatch across all tested thresholds ($T \in \{60, 65, 70, 75, 80\}$). Its inclusion under $[60, 70)$ in v2 was a typographical misclassification.

---

### B. Resolution of the 31 Cases vs. (16 + 6 + 7) Subgroup Discrepancy:
In v2, the report noted that 31 mutated venues fell in $[60, 80)$, but listed subgroup counts of $16 + 6 + 7 = 29$, creating an apparent arithmetic inconsistency ($31 \ne 29$).

Auditing the raw 100 `wrong_venue` instances reveals the exact distinction between **raw venue score partitions** and **marginal citation-detection impact**:

#### 1. Raw Continuous Venue Score Distribution ($N = 100$ Wrong Venue Citations):
Evaluating `compare_venues()` across all 100 `wrong_venue` citations partitions the instances as follows:
- **Score $< 60$:** **42 cases** (e.g., CID 460 at 47.27)
- **Score $\in [60, 70)$:** **17 cases** (scores range from 61.02 to 68.18)
- **Score $\in [70, 75)$:** **7 cases** (scores range from 70.18 to 73.17)
- **Score $\in [75, 80)$:** **7 cases** (scores range from 76.06 to 79.01)
- **Score $\ge 80$:** **27 cases** (scores of 80.0, 87.1, or 100.0)
- **Total cases in critical band $[60, 80)$:**
  $$17 + 7 + 7 = \mathbf{31\text{ cases}}$$

The count of 31 cases in $[60, 80)$ is mathematically exact.

#### 2. Marginal Citation-Detection Impact ($16 + 6 + 7 = 29$ Dynamic Classification Flips):
In the CiteGuard verification pipeline, a citation is classified as accurate only if **all** metadata checks pass:
$$\text{citation\_accurate} = \text{paper\_exists} \land \text{title\_check} \land \text{author\_check} \land \text{year\_check} \land \text{venue\_check} \land \text{doi\_check}$$

When auditing the 31 citations in $[60, 80)$, exactly **two citations** possess compounding secondary errors:
1. **CID 497** (Venue score: $65.71 \in [60, 70)$): Suffers from an independent **Publication Year Mismatch** (`year_match = False`). Even at $T=60$ where its venue score ($65.71 \ge 60$) would have passed `venue_check`, it is still correctly classified as hallucinated (`prediction = 1`) due to the year mismatch.
2. **CID 483** (Venue score: $70.45 \in [70, 75)$): Suffers from an independent **Publication Year Mismatch** (`year_match = False`). It is classified as hallucinated at all thresholds $T \ge 60$ regardless of venue score.

Consequently, the number of citations whose final classification decision is **exclusively governed** by the venue threshold is $31 - 2 = \mathbf{29\text{ cases}}$:
- **Threshold transition $T = 60 \to 70$:** $17 - 1 = \mathbf{16\text{ dynamic flips}}$ (8 flip at $T=65$, 8 flip at $T=70$). Detection rises from $46/100 \to 62/100$ ($+16$).
- **Threshold transition $T = 70 \to 75$:** $7 - 1 = \mathbf{6\text{ dynamic flips}}$ (CIDs 421, 422, 471, 472, 476, 484). Detection rises from $62/100 \to 68/100$ ($+6$).
- **Threshold transition $T = 75 \to 80$:** $7 - 0 = \mathbf{7\text{ dynamic flips}}$ (CIDs 414, 417, 426, 435, 453, 486, 488). Detection rises from $68/100 \to 75/100$ ($+7$).
- **Total dynamically flipping citations across $[60, 80)$:**
  $$16 + 6 + 7 = \mathbf{29\text{ citations}}$$

#### 3. Complete Reconciled Sensitivity Table ($N = 600$):
```
========================================================================================================================
TRUE THRESHOLD SENSITIVITY (CiteGuard + Author + Venue Fix, N = 600)
========================================================================================================================
Threshold   Accuracy   Precision   Recall      F1-Score    TP     FP    TN    FN    Valid Acc    Wrong Venue Detection
------------------------------------------------------------------------------------------------------------------------
T = 60      88.17%     98.42%      87.20%      92.47%      436    7     93    64    93/100       46/100 (+8 vs base)
T = 65      89.50%     98.45%      88.80%      93.38%      444    7     93    56    93/100       54/100 (+16 vs base)
T = 70      90.83%     98.47%      90.40%      94.26%      452    7     93    48    93/100       62/100 (+24 vs base)
T = 75      91.83%     98.49%      91.60%      94.92%      458    7     93    42    93/100       68/100 (+30 vs base)
T = 80      93.00%     98.52%      93.00%      95.68%      465    7     93    35    93/100       75/100 (+37 vs base)
========================================================================================================================
```

---

## 2. Item 2: Recalculated McNemar Test of Paired Classification Correctness

All 600 rows in `experimental_detailed_results.csv` were verified for strict 1-to-1 alignment by stable `citation_id` and `ground_truth`.

### Definition & Scope:
McNemar's test evaluates paired nominal observations on identical instances. In this context, it tests **paired classification correctness** ($1 = \text{correct}, 0 = \text{incorrect}$) between **Current CiteGuard (Baseline)** and **CiteGuard + Author + Venue Fix (Combined Fix)** across all 600 benchmark citations.
> [!NOTE]
> This is a formal hypothesis test of **instance-level paired classification correctness**, testing the null hypothesis of marginal homogeneity ($H_0: P(\text{Baseline}=1, \text{Combined}=0) = P(\text{Baseline}=0, \text{Combined}=1)$). It is not an omnibus test of aggregate harmonic F1 scores.

### $2 \times 2$ Contingency Table:
```
                                Combined Correct (1)    Combined Incorrect (0)    Total
Baseline Correct (1):                 n11 = 437                 n10 = 0            437
Baseline Incorrect (0):               n01 = 108                 n00 = 55           163
Total:                                    545                       55             600
```

### Discordant Pair Analysis:
- $n_{01} = 108$: Baseline incorrect $\to$ Combined configuration correct (**108 citations improved**).
- $n_{10} = 0$: Baseline correct $\to$ Combined configuration incorrect (**0 regressions**).
- Total discordant pairs: $n_{01} + n_{10} = 108$.

### Statistical Test Statistics:
1. **Edwards Continuity-Corrected Chi-Square:**
   $$\chi^2 = \frac{(|n_{01} - n_{10}| - 1)^2}{n_{01} + n_{10}} = \frac{(|108 - 0| - 1)^2}{108} = \frac{107^2}{108} = 106.0093 \quad (df = 1)$$
2. **Asymptotic $p$-value:**
   $$p = 7.34 \times 10^{-25} \quad (\chi^2 = 106.01, df = 1)$$
3. **Exact Two-Sided Binomial Test:**
   Under the null hypothesis $H_0$, the number of discordant successes follows $\text{Binomial}(n = 108, p = 0.5)$.
   $$p = 2 \times \sum_{k=0}^{\min(n_{01}, n_{10})} \binom{108}{k} (0.5)^{108} = 2 \times (0.5)^{108} = 6.1630 \times 10^{-33}$$

The improvement in instance-level classification correctness is statistically significant ($p = 6.16 \times 10^{-33}$).

---

## 3. Item 3: Recalculated Confusion Matrices & Confidence Intervals

All metrics were independently recalculated from raw instance-level predictions and ground-truth labels ($N = 600$ per configuration):
- **Accuracy Intervals:** Wilson Score Interval with continuity ($\alpha = 0.05, z = 1.95996$).
- **F1 Intervals:** Non-parametric Bootstrap Resampling ($B = 10,000$ iterations, percentile method, random seed 42).

```
====================================================================================================================================
AUDITED CONFUSION MATRICES & 95% CONFIDENCE INTERVALS (N = 600)
====================================================================================================================================
Configuration                   TP    FP   TN   FN    Accuracy   95% Wilson CI          Precision   Recall     F1-Score   95% Bootstrap CI (10k)
------------------------------------------------------------------------------------------------------------------------------------
Current CiteGuard (Baseline)    344   7    93   156   72.83%     [69.14%, 76.24%]       98.01%      68.80%     80.85%     [77.95%, 83.56%] (SE 1.44%)
CiteGuard + Author Fix          428   7    93   72    86.83%     [83.89%, 89.31%]       98.39%      85.60%     91.55%     [89.59%, 93.33%] (SE 0.95%)
CiteGuard + Venue Fix           368   7    93   132   76.83%     [73.29%, 80.03%]       98.13%      73.60%     84.11%     [81.48%, 86.59%] (SE 1.31%)
CiteGuard + Author + Venue Fix  452   7    93   48    90.83%     [88.26%, 92.89%]       98.47%      90.40%     94.26%     [92.69%, 95.70%] (SE 0.77%)
====================================================================================================================================
```

All 95% confidence intervals between Baseline ($[77.95\%, 83.56\%]$) and Combined Fix ($[92.69\%, 95.70\%]$) are strictly non-overlapping.

---

## 4. Item 4: Scientific Reproduction Boundary

> [!CAUTION]
> **Scientific Reproduction Boundary:**  
> The Combined Fix achieves **90.83% Accuracy** and **94.26% F1-score** on the modern codebase with the reproducible cache. While this aligns closely with the results published in IEEE ICDDS 2026 Table I (90.33% Accuracy, 94.15% F1), it does **not** represent an independent rerun of the historical August 2026 experiment, which ran prior to DOI candidate injection and under an earlier dependency environment. The saved paper artifacts in `targeted_fixes_detailed.csv` and `final_results_corrected.csv` remain intact as the historical record.

---

## 5. Item 5: Exact Files and Staging Manifest for Merge Approval

The following files constitute the exact set of changes on branch `experiment/venue-fix`. **No merge or commit will occur without explicit user approval.**

### Production Code Modifications:
1. [`backend/app/services/candidate_ranker.py`](file:///c:/Users/A%20S%20Nemitha/Desktop/CiteGuard/backend/app/services/candidate_ranker.py):
   - Lines 41 & 100: Passes `use_venue_fix=use_venue_fix` explicitly into `compare_venues()`, ensuring ranking respects the Venue Fix flag.
2. [`backend/app/services/similarity_service.py`](file:///c:/Users/A%20S%20Nemitha/Desktop/CiteGuard/backend/app/services/similarity_service.py):
   - Lines 351–355: Enforces exact normalized match for `"nature"` and `"science"` alias keys, eliminating false matches against sister journals (e.g. `Nature Chemistry`, `Science Advances`).
   - Lines 380–386: Implements strict `fuzz.token_sort_ratio(n1, n2) >= 70` comparison under `use_venue_fix=True`, removing permissive substring containment.
3. [`datasets/citation_verification/run_reproducible_evaluation.py`](file:///c:/Users/A%20S%20Nemitha/Desktop/CiteGuard/datasets/citation_verification/run_reproducible_evaluation.py):
   - Lines 44 & 47: Accepts `*args, **kwargs` in mock functions, preventing signature mismatch exceptions.
4. [`.gitignore`](file:///c:/Users/A%20S%20Nemitha/Desktop/CiteGuard/.gitignore):
   - Ignores scratch scripts and temporary experiment artifacts.

### Supporting Diagnostic & Verification Files:
1. [`reproduce_icdds2026_benchmark.py`](file:///c:/Users/A%20S%20Nemitha/Desktop/CiteGuard/reproduce_icdds2026_benchmark.py): Read-only audit script for saved camera-ready paper artifacts.
2. [`datasets/citation_verification/experiments_venue_fix/`](file:///c:/Users/A%20S%20Nemitha/Desktop/CiteGuard/datasets/citation_verification/experiments_venue_fix/):
   - `test_venue_fixes.py`: Regression unit tests (4/4 passing).
   - `run_venue_experiment.py`: Experimental reproduction harness.
   - `experimental_detailed_results.csv`: Citation-level predictions for all 2,400 configuration rows.
   - `experimental_summary.json`: Detailed summary metrics.
   - `validation/test_venue_generalization.py`: Independent 40-pair generalization test suite (95% accuracy, 5% FAR).
   - `validation/FINAL_VALIDATION_REPORT_V3.md`: This comprehensive audit document.

---

## 6. Item 6: Honest Reviewer-Response Status Checklist

In accordance with user instructions, all reviewer items requiring external baseline execution, visual assets, or broader corpus collection remain marked **In Progress**:

| Reviewer Item | Status | Completed Evidence | Remaining Work Required | Supporting Artifact |
| :--- | :---: | :--- | :--- | :--- |
| **1. Figure 4 readability** | **In Progress** | Underlying confusion matrix data re-verified and formatted. | Re-render using high-DPI vector export (PDF/SVG) with $\ge 12\text{pt}$ typography and inspect visually. | `final_confusion_matrices.png` |
| **2. Precision vs. recall trade-off** | **Complete** | High precision ($98.47\%$) prioritized to prevent false accusations; recall ($90.40\%$) captures perturbations. | Add formal 2-paragraph discussion to Section VI-A of manuscript revision. | `experimental_summary.json` |
| **3. Benchmark construction & labelling** | **In Progress** | 600 benchmark citations verified and categorized into 6 balanced types. | Draft formal annotation protocol and human curation guidelines in supplementary material. | `hard_citation_test_dataset.csv` |
| **4. Class imbalance & confidence intervals** | **Complete** | 5:1 ratio evaluated. Computed 95% Wilson CIs for accuracy and 10k bootstrap CIs for F1; executed McNemar's test ($p < 10^{-32}$). | Incorporate audited $\pm 95\%$ CIs and McNemar test statistics into Camera-Ready Table I. | `confidence_intervals.json` |
| **5. Threshold/weight justification & sensitivity** | **Complete** | Verified sensitivity across $T \in [60, 80]$; score distributions documented; demonstrated necessity of `VENUE_ALIASES`. | Insert sensitivity curve table and score distribution analysis in camera-ready appendix. | `FINAL_VALIDATION_REPORT_V3.md` |
| **6. Fair comparison with CiteCheck / baselines** | **In Progress** | Created internal DOI-only and CrossRef metadata-only ablation baselines. | Execute fair direct comparison against CiteCheck/Scite on identical frozen cache. | `baseline_doi.py`, `baseline_crossref_metadata.py` |
| **7. API failures & metadata drift** | **In Progress** | 30-day SQLite TTL cache expiry identified; offline cache established. | Perform systematic fault-injection stress testing for live API drift and service timeouts. | `cache_service.py` |
| **8. Larger, more diverse evaluation data** | **In Progress** | Evaluated 40-pair independent venue generalization test (FAR dropped $85\% \to 5\%$). | Expand benchmark to multi-disciplinary domains (PubMed, Law) with $\ge 1,000$ instances. | `test_venue_generalization.py` |

---

## 7. Final Summary & Go/No-Go Recommendation

### Measured Basis:
1. **Discrepancies Fully Resolved:** Both the CID 460 band placement and the $31$ vs $16 + 6 + 7$ subgroup counts have been completely explained through the raw continuous score distribution ($17 + 7 + 7 = 31$) versus the marginal classification impact ($16 + 6 + 7 = 29$, accounting for 2 citations with independent year errors).
2. **Statistically Significant Gain:** McNemar's paired classification correctness test yields $\chi^2 = 106.01, df = 1, p = 6.16 \times 10^{-33}$ (108 improvements, 0 regressions).
3. **Generalization Demonstrated:** 40-pair independent generalization test shows 95% accuracy and a False Acceptance Rate drop from 85% to 5%.
4. **Codebase Containment:** All changes remain strictly on branch `experiment/venue-fix`. Production `main` has not been altered.

**Recommendation:** The Venue Fix is technically sound, empirically verified, and statistically validated. It is **READY FOR MERGE** whenever you explicitly approve.
