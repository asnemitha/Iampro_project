# Final Scientific Review & Response to Reviewers (ICDDS 2026)

**Manuscript Reference**: CiteGuard: Real-Time Scholarly Reference Verification Pipeline  
**Conference**: IEEE International Conference on Data Driven Security (ICDDS 2026)  
**Document Status**: Final Reviewer Response (Camera-Ready & Reviewer Dialog)  
**Scope Notice**: This document provides a rigorous, point-by-point response to reviewer feedback based strictly on saved empirical artifacts, frozen audit reports, and verified code execution. It explicitly separates the accepted paper's historical camera-ready findings from post-acceptance controlled diagnostic evaluations (Benchmark V2.0). It avoids unsupported claims of external generalization, completed comparisons with external systems, or universal threshold optimality. Reviewer comments are presented as thematic summaries of feedback received.

---

## Executive Summary of Methodological Stance

We thank the reviewers and program chairs for their constructive evaluations and insightful questions. The reviewer feedback focused on six key areas:
1. **Benchmark Construction & Label Provenance**: Sourcing of the 600 citations, perturbation mechanics, and investigation into potential label noise.
2. **Evaluation Baselines & Progression**: Distinguishing the accepted paper's published camera-ready results from the controlled diagnostic Benchmark V2.0 evaluation and the independent multidisciplinary holdout benchmark.
3. **Class Distribution & Metric Selection**: Addressing the 5:1 class ratio (500 hallucinated vs. 100 valid) using balanced performance metrics.
4. **Threshold Sensitivity & Statistical Rigor**: Reporting empirical sensitivity analysis for the venue threshold ($\tau$) directly from saved artifacts and quantifying sampling uncertainty via confidence intervals.
5. **Venue Validation Limitations & Metadata Sparsity**: Explaining the 23 remaining venue false negatives (missed hallucinations) and documenting the missing-metadata fallback policy.
6. **Prior Work & Disciplinary Generalization**: Delineating completed architectural distinctions from unperformed empirical comparisons (e.g., head-to-head benchmarking with CiteCheck), and evaluating cross-disciplinary generalization across four academic disciplines via an independent 400-citation holdout benchmark.

Below, we address each concern using exact numbers verified against saved repository artifacts.

---

## Point-by-Point Reviewer Responses

### Reviewer Concern 1 (Summary): Benchmark Construction, Provenance, and Label Quality
> **Reviewer Concern Summary**: *The 600-citation benchmark construction is insufficiently documented. Clarification is requested on how citations were sourced, how perturbations were generated, and whether any generated citations were ambiguous or noisy.*

#### 1. Professional Response
The 600-citation benchmark was designed as a multi-category stress test anchored on genuine scholarly publications. Following reviewer questions regarding label validity, we performed an exhaustive, byte-level read-only audit of the original benchmark (`hard_citation_test_dataset.csv`). This audit identified **24 label-noise records (4.0%)** where synthetic perturbations resulted in no textual change ("no-op perturbations"):
- **7 Author No-Ops (`corrupted_authors`)**: The donor paper assigned by the index offset happened to share the same first author as the source paper, leaving the author roster textually identical to the genuine paper.
- **17 Venue No-Ops (`wrong_venue`)**: The donor paper shared the identical publication venue as the source paper, leaving the venue string unmutated.

Because these 24 citations remained textually identical to valid papers, any sound verification pipeline properly identified them as genuine records, resulting in synthetic False Negatives (missed detections) against the hallucinated label.

To quantify pipeline performance free from this label noise, we constructed **Benchmark V2.0** (`hard_citation_test_dataset_v2.csv`). V2.0 preserves the exact experimental design of V1.0 (the same 100 seed papers, the same six categories of 100 citations each, and the same $\pm 1$ year offset), but advances donor selection until the replacement field strictly differs from the source under normalized comparison.

#### 2. Completed Evidence Supporting Response
- **Seed Provenance**: Exactly 100 genuine papers indexed in Crossref across computer science and machine learning, with complete titles, author rosters, years, venues, and canonical DOIs.
- **Category Composition ($N=100$ each)**: `valid` (100), `doi_mismatch` (100), `corrupted_authors` (100), `wrong_year` (100), `wrong_venue` (100), and `plausible_fabricated` (100).
- **Audit Reports & Provenance**: Serialized in `BENCHMARK_V2_AUDIT_REPORT.md`, `v1_v2_reconciliation_table.csv`, and `EVALUATION_V2_AUDIT_REPORT.md`.
- **Pre-Commit Validation**: Non-bypassable checks confirmed zero duplicate citation strings, zero cross-label collisions, zero no-ops, and 100% metadata completeness.

#### 3. Honest Statement of Remaining Limitations
- Benchmark V2.0 is an in-distribution controlled correction using the original 100 seed papers; it does not constitute an independent, external replication dataset.
- Synthetic perturbations, while controlled, model discrete single-field errors and do not capture all complex forms of LLM-generated hallucination (such as blended multi-paper citations or fictitious page numbers).

#### 4. Actionable Manuscript Changes Needed
- Add Section IV-B ("Benchmark Provenance and Generation Protocol") detailing seed paper selection, perturbation operators, and validation filters.
- Include a summary table in the supplementary materials listing the 24 repaired records, original versus mutated strings, donor DOIs, and mutation rules.

---

### Reviewer Concern 2 (Summary): Relationship Between Camera-Ready Results and Benchmark V2.0
> **Reviewer Concern Summary**: *The accepted manuscript reports an accuracy of 90.33% and F1 of 94.15% with 33 False Negatives. Clarification is requested on how this relates to the 94.50% accuracy and 26 False Negatives reported on V2.0, and whether label correction explains the entire difference.*

#### 1. Professional Response
We clarify that **the historical results in the accepted manuscript (90.33% accuracy, 94.15% F1, 33 False Negatives) represent the archival baseline of the conference proceedings**. Benchmark V2.0 is a post-acceptance controlled diagnostic evaluation on the corrected dataset; it does not replace or retroactively modify the published paper's historical record.

Furthermore, we do **not** claim that label correction alone caused the performance change between the published paper and V2.0. The transition involves two distinct, measurable phases:
1. **Codebase Normalizer Evolution**: Between the August 2026 camera-ready freeze and the final venue-fix implementation (commit `d6893ba`), CiteGuard's multi-source metadata normalizer and candidate ranker were overhauled. This improved valid-citation specificity substantially (reducing False Positives from 25 to 7, bringing Specificity from 75.0% to 93.0%). Under this modernized pipeline, baseline venue False Negatives on V1.0 shifted from 15 to 38 under strict matching.
2. **Label-Noise Correction**: Evaluating the modern pipeline on Benchmark V2.0 eliminated the 24 no-ops, directly converting 22 former False Negatives into True Positives (author FNs: $9 \rightarrow 2$; venue FNs: $38 \rightarrow 23$), reducing total False Negatives from 48 to 26.

#### 2. Completed Evidence Supporting Response
Reconciled across the four versioned tiers under identical verification thresholds ($\tau = 70.0$):

$$\begin{array}{lcccc|ccc}
\hline
\textbf{Evaluation Phase} & \textbf{Total TP} & \textbf{Total FN} & \textbf{FP} & \textbf{TN} & \textbf{Accuracy} & \textbf{F1 Score} & \textbf{Primary Context} \\
\hline
\text{1. Accepted Camera-Ready (V1.0 Historical)} & 467 & 33 & 25 & 75 & 90.33\% & 94.15\% & \text{Archival freeze (Aug 17, 2026); FP=25} \\
\text{2. Modern Committed Pipeline on V1.0 Baseline} & 452 & 48 & 7 & 93 & 90.83\% & 94.26\% & \text{Committed code (commit d6893ba); FP=7} \\
\text{3. Modern Pipeline on V2.0 (benchmark\_v2)} & 474 & 26 & 7 & 93 & 94.50\% & 96.64\% & \text{Controlled diagnostic on same seeds} \\
\textbf{4. Independent Multidisciplinary Holdout} & \mathbf{284} & \mathbf{16} & \mathbf{7} & \mathbf{93} & \mathbf{94.25\%} & \mathbf{96.11\%} & \mathbf{Disjoint\ seeds\ across\ 4\ disciplines\ (N=400)} \\
\hline
\end{array}$$

#### 3. Honest Statement of Remaining Limitations
- Retrospective code and benchmark audits cannot retroactively change the printed conference proceedings.
- The progression demonstrates that pipeline improvements (normalizers), benchmark improvements (label quality), and cross-disciplinary holdout validation provide complementary, distinct evidence.

#### 4. Actionable Manuscript Changes Needed
- Add a paragraph in Section V ("Results and Discussion") presenting the four-tier progression table, explicitly distinguishing the archival camera-ready baseline from the modern codebase, the clean-label diagnostic, and the independent multidisciplinary holdout.

---

### Reviewer Concern 3 (Summary): Class Imbalance in Benchmark (500 Hallucinated vs. 100 Valid Citations)
> **Reviewer Concern Summary**: *The 5:1 ratio of hallucinated to valid citations is unbalanced. The authors should address whether this class distribution distorts accuracy and F1 metrics and report performance under balanced criteria.*

#### 1. Professional Response
The 5:1 ratio ($N=500$ hallucinated, $N=100$ valid) was selected as a stress-testing experimental design to evaluate **five distinct hallucination mechanisms** (100 citations per mechanism: DOI mismatch, corrupted authors, wrong year, wrong venue, plausible fabrication) against a single control group of 100 genuine citations, providing equal sample sizes across the five error categories ($N=100$ per error type).

To ensure performance is not distorted by class prevalence, we evaluate CiteGuard using prevalence-independent and balanced metrics on Benchmark V2.0:
- **Sensitivity / Recall (Hallucinated Class)**: $474 / 500 = \mathbf{94.80\%}$
- **Specificity (Valid Class)**: $93 / 100 = \mathbf{93.00\%}$
- **Balanced Accuracy** ($\frac{\text{Sensitivity} + \text{Specificity}}{2}$): $\mathbf{93.90\%}$
- **Positive Class F1 (Hallucination Detection)**: $\mathbf{96.64\%}$ (Precision: 98.54%, Recall: 94.80%)
- **Negative Class F1 (Valid Citation Acceptance)**: $\mathbf{84.93\%}$ (Precision: 78.15%, Recall: 93.00%)
- **Macro-Averaged F1**: $\mathbf{90.78\%}$
- **95% Confidence Intervals**: Accuracy $[92.38\%,\ 96.06\%]$ (Wilson score); Positive F1 $[95.46\%,\ 97.73\%]$ (Bootstrap, $B=10{,}000$).

These balanced metrics confirm that CiteGuard achieves high discrimination across both classes ($>93\%$ sensitivity and specificity) and does not rely on positive-class prevalence.

#### 2. Completed Evidence Supporting Response
- All 2,400 per-record predictions in `targeted_fixes_detailed_v2.csv` confirm exactly $\text{TP} + \text{FN} = 500$ and $\text{FP} + \text{TN} = 100$.
- Recomputed exact confusion matrix values and verified symmetric class metrics without error.

#### 3. Honest Statement of Remaining Limitations
- In operational LLM generation, hallucination prevalence is typically lower than 83.3% (often ranging between 10% and 40% depending on the model and prompt). In lower-prevalence deployments, precision will depend heavily on the False Positive Rate ($7.0\%$ in our evaluation).
- Confidence intervals reflect sampling uncertainty within this 600-citation sample and do not eliminate selection bias inherent in the seed corpus.

#### 4. Actionable Manuscript Changes Needed
- Update Table I to report Balanced Accuracy ($93.90\%$), Specificity ($93.00\%$), and Macro-F1 ($90.78\%$) alongside positive-class Precision, Recall, and F1.
- Add an explicit discussion on operational prevalence assumptions in Section V-C.

---

### Reviewer Concern 4 (Summary): Threshold Sensitivity and Statistical Rigor
> **Reviewer Concern Summary**: *The venue matching threshold $\tau = 70.0$ appears arbitrarily chosen. An empirical sensitivity analysis and formal confidence intervals should be provided.*

#### 1. Professional Response
The threshold $\tau = 70.0$ was established during exploratory pipeline development to balance sensitivity to venue substitutions against tolerance for legitimate bibliographic publisher variations (e.g., abbreviations and imprint changes).

Direct inspection of the saved exploratory threshold evaluation artifact (`datasets/citation_verification/experiments_venue_fix/validation/threshold_sensitivity.json`), which evaluated $\tau \in \{60, 65, 70, 75, 80\}$ on the V1.0 benchmark, yields the following exact empirical results:

$$\begin{array}{c|cccc|cc|cc}
\hline
\textbf{Threshold } (\tau) & \textbf{TP} & \textbf{TN} & \textbf{FP} & \textbf{FN} & \textbf{Accuracy} & \textbf{F1 Score} & \textbf{Venue Det.} & \textbf{Valid Acc.} \\
\hline
\multicolumn{9}{l}{\textbf{Configuration: CiteGuard + Author + Venue Fix}} \\
\tau = 60.0 & 451 & 93 & 7 & 49 & 90.67\% & 94.15\% & 61 / 100 & 93 / 100 \\
\tau = 65.0 & 451 & 93 & 7 & 49 & 90.67\% & 94.15\% & 61 / 100 & 93 / 100 \\
\mathbf{\tau = 70.0} & \mathbf{451} & \mathbf{93} & \mathbf{7} & \mathbf{49} & \mathbf{90.67\%} & \mathbf{94.15\%} & \mathbf{61 / 100} & \mathbf{93 / 100} \\
\tau = 75.0 & 451 & 93 & 7 & 49 & 90.67\% & 94.15\% & 61 / 100 & 93 / 100 \\
\tau = 80.0 & 451 & 93 & 7 & 49 & 90.67\% & 94.15\% & 61 / 100 & 93 / 100 \\
\hline
\multicolumn{9}{l}{\textbf{Configuration: CiteGuard + Venue Fix}} \\
\tau = 60.0 & 367 & 93 & 7 & 133 & 76.67\% & 83.98\% & 61 / 100 & 93 / 100 \\
\tau = 65.0 & 367 & 93 & 7 & 133 & 76.67\% & 83.98\% & 61 / 100 & 93 / 100 \\
\mathbf{\tau = 70.0} & \mathbf{367} & \mathbf{93} & \mathbf{7} & \mathbf{133} & \mathbf{76.67\%} & \mathbf{83.98\%} & \mathbf{61 / 100} & \mathbf{93 / 100} \\
\tau = 75.0 & 367 & 93 & 7 & 133 & 76.67\% & 83.98\% & 61 / 100 & 93 / 100 \\
\tau = 80.0 & 367 & 93 & 7 & 133 & 76.67\% & 83.98\% & 61 / 100 & 93 / 100 \\
\hline
\end{array}$$

*Empirical Analysis & Documented Discrepancy*:
- **Artifact Verification**: Across the tested range $\tau \in [60.0, 80.0]$ on V1.0, metrics for both configurations remain strictly invariant because the token sort ratios for perturbed venues in this dataset fall either below 60.0 or above 80.0. An earlier informal working draft mixed V2.0 counts with hypothetical entries for $\tau \in \{75, 80, 85\}$; the table above restores the exact numbers from `threshold_sensitivity.json`.
- **Impact of Alias Expansion**: The artifact also records that when alias expansion is disabled (`without_alias_lookup`), exactly 10 valid citations are rejected across all thresholds ($60 \le \tau \le 80$), proving that semantic alias expansion is essential to preserving specificity.

Statistical uncertainty for primary metrics is formally characterized using:
- **Accuracy**: 95% Wilson score continuity interval.
- **F1 Score**: 95% non-parametric bootstrap interval ($B = 10{,}000$ resamples, seed 42).

#### 2. Completed Evidence Supporting Response
- Artifact: `datasets/citation_verification/experiments_venue_fix/validation/threshold_sensitivity.json`.
- Artifact: `datasets/citation_verification/experiments_venue_fix/validation/confidence_intervals.json`.
- Wilson and bootstrap intervals recomputed and verified across all four configurations.

#### 3. Honest Statement of Remaining Limitations
- The threshold sensitivity analysis in `threshold_sensitivity.json` represents exploratory tuning on the existing benchmark rather than locked-box validation on an independent holdout dataset.
- The threshold $\tau = 70.0$ should be regarded as an empirically supported operating point for computer science literature, not a universally optimal constant across all scholarly domains.

#### 4. Actionable Manuscript Changes Needed
- Add Section V-D ("Threshold Sensitivity and Operating Characteristics") summarizing the empirical $\tau \in [60.0, 80.0]$ evaluation and the impact of alias expansion.
- Incorporate 95% Wilson and bootstrap confidence intervals into all summary tables and figures.

---

### Reviewer Concern 5 (Summary): Venue Validation Edge Cases and Metadata Sparsity
> **Reviewer Concern Summary**: *Clarification is requested on what explains the remaining 23 venue false negatives in Benchmark V2.0 and how CiteGuard handles missing metadata in scholarly indexes.*

#### 1. Professional Response
A False Negative in our evaluation represents a **hallucinated citation that was incorrectly accepted as valid** (`ground_truth = 1`, `prediction = 0`). Our audit evaluated every one of the 23 remaining venue False Negatives directly against production `compare_venues(..., use_venue_fix=True, threshold=70.0)`:

1. **Missing Metadata Permissive Fallback (2 cases, V2 IDs 152 and 588)**:
   - The genuine Crossref records for these papers lack `container-title` and `publisher` entries (`venue = ""`).
   - Per production design (lines 337–338 of `similarity_service.py`), when metadata is missing from scholarly indexes, CiteGuard falls back to a permissive match (`return True, 100.0`). This architectural choice prevents unfairly penalizing valid citations when public indexing records are incomplete.
2. **Normalized Acronym & Stopword Collisions (3 cases)**:
   - Example: Mutated citation venue `"Journal of Natural Language Processing"` versus metadata venue `"Natural Language Processing"`.
   - After stripping standard stopwords (`"journal of"`, `"proceedings of"`), both strings normalize to `"natural language processing"`, yielding an exact normalized match ($100.0\%$).
3. **High Lexical Token Overlap (18 cases, Scores 70.18% – 87.10%)**:
   - In computer science, distinct book series and conference imprints often share substantial terminology.
   - Example 1 (V2 ID 432): Mutated citation `"Deep Learning with Python"` versus metadata `"Deep Learning on Windows"`. Token sort ratio = **77.55%** ($> 70.0$ threshold) $\rightarrow$ accepted as matching.
   - Example 2 (V2 ID 177): Mutated citation `"Journal of Natural Language Processing"` versus metadata `"Natural Language Processing and Applications"`. Token sort ratio = **76.06%** ($> 70.0$ threshold) $\rightarrow$ accepted as matching.
   - Example 3 (V2 ID 256): Mutated citation `"Encyclopedia of Data Science and Machine Learning"` versus metadata `"Encyclopedia of Machine Learning"`. Token sort ratio = **79.01%** ($> 70.0$ threshold) $\rightarrow$ accepted as matching.

#### 2. Completed Evidence Supporting Response
- Production code execution verified in `EVALUATION_V2_AUDIT_REPORT.md` (Section 4).
- Exact similarity scores and normalized string outputs documented for all 23 records.

#### 3. Honest Statement of Remaining Limitations
- Lexical token-sorting cannot distinguish between closely related book titles or specialized tracks within the same field without external domain ontologies or canonical publication ISSNs.
- Permissive fallback on missing metadata represents a conscious trade-off favoring high specificity (low False Positives on valid citations) over exhaustive hallucination detection.

#### 4. Actionable Manuscript Changes Needed
- Expand Section V-E ("Error Analysis and Failure Modes") to provide a taxonomy of the 23 venue False Negatives: metadata sparsity ($8.7\%$, 2/23), stopword collisions ($13.0\%$, 3/23), and shared topical vocabulary ($78.3\%$, 18/23).

---

### Reviewer Concern 6 (Summary): Comparison with Prior Systems and Disciplinary Generalization
> **Reviewer Concern Summary**: *The authors should clarify how CiteGuard compares to existing systems like CiteCheck and address empirical generalization across academic disciplines beyond computer science.*

#### 1. Professional Response
We explicitly separate our completed empirical evidence from published literature and newly evaluated cross-disciplinary validation:

1. **Comparison with CiteCheck**:
   - *Status of Head-to-Head Empirical Benchmarking*: A reproducible empirical head-to-head comparison against CiteCheck could not be completed in the current repository environment. The CiteCheck software package (`FirstPrinciplesLabs/citecheck`) is not present or installed locally, and its published verification pipeline requires external commercial LLM API credentials (e.g., Anthropic Claude or OpenAI) alongside unthrottled live network access to external scholarly APIs. Furthermore, the repository's frozen cache (`reproducible_api_cache_v2.json`) was constructed specifically for CiteGuard's query endpoints and cannot represent CiteCheck's queries or LLM responses. In accordance with strict scientific integrity guidelines, we do not fabricate a proxy script to substitute for CiteCheck.
   - *Methodological & Architectural Comparison (from Published Literature)*: Based on its published literature (*Khajavi et al., 2025*), CiteCheck operates as an LLM-in-the-loop framework combining regex/LLM parsing, an external API cascade (arXiv, CrossRef, Semantic Scholar, OpenAlex), a structured LLM verifier, and an optional second-pass reviewer LLM to produce a three-way classification (`exact_match`, `minor_hallucination`, `major_hallucination`), evaluated in its paper on a 982-citation physics dataset. In contrast, CiteGuard evaluates binary validity on a 600-citation computer science dataset, employing multi-source consensus retrieval (Crossref, OpenAlex, Semantic Scholar) and deterministic string similarity (token-sort ratio, author-set normalization, and venue alias expansion) for its classification decisions. These distinctions reflect published architectural differences rather than head-to-head empirical measurements.
   - *Internal Baseline Ablation (Identifier Existence Check)*: To illustrate the operational limitation of naive identifier resolution, we evaluated a single-source DOI existence baseline (`baseline_doi.py`). As directly verified from `datasets/citation_verification/baseline_results.csv`, checking DOI existence alone achieves exactly **40.00% Recall** ($\text{TP}=200, \text{FN}=300, \text{FP}=0, \text{TN}=100$, Accuracy: 50.00%, Precision: 100.00%, Specificity: 100.00%, F1: 57.14%). While it detects fake DOIs (100/100) and completely fabricated citations (100/100), it fails to detect all 300 citations where a valid DOI is coupled with corrupted authors (0/100), corrupted venues (0/100), or wrong years (0/100). We emphasize that this is an internal ablation baseline illustrating why granular bibliographic metadata verification is necessary, and is **not** an implementation or evaluation of CiteCheck (which also performs multi-field candidate inspection).

2. **Independent Multidisciplinary Generalization Benchmark**:
   - *Addressing Disciplinary Scope*: While the accepted paper and Benchmark V2.0 were restricted to 100 Computer Science and Machine Learning seed papers, we directly addressed reviewer requests for broader disciplinary evaluation by constructing an **Independent Multidisciplinary Holdout Benchmark** of **400 citations** (`datasets/citation_verification/independent_holdout/`).
   - *Strict Disjointness and Provenance*: The holdout was harvested from Crossref across four major scholarly domains (25 genuine seed papers per discipline; 100 total):
     1. **Computer Science** (algorithms, systems, AI)
     2. **Medicine & Biomedical Sciences** (clinical trials, oncology, immunology)
     3. **Natural Sciences** (physics, chemistry, materials science)
     4. **Humanities & Social Sciences** (economics, sociology, history, psychology)
     A rigorous programmatic audit confirmed **zero overlapping DOIs, zero overlapping titles, and zero overlapping citation strings** with Benchmarks V1.0/V2.0.
   - *Benchmark Composition*: Following a pre-registered sampling protocol (`SAMPLING_AND_ANNOTATION_PROTOCOL.md`), the 400 citations comprise 100 genuine citations (25 per discipline) and 300 programmatically perturbed citations (75 per discipline, 60 per error type across `corrupted_authors`, `wrong_venue`, `wrong_year`, `doi_mismatch`, and `plausible_fabricated`). Zero no-op mutations exist across all 300 perturbations.
   - *Empirical Generalization Results*: Under the exact frozen production thresholds ($\tau = 70.0$, title threshold 80.0) without any discipline-specific parameter tuning, CiteGuard's Combined configuration demonstrated robust, uniform performance across all four disciplines:
     * **Computer Science ($N=100$)**: 92.00% Accuracy, 94.59% F1 (Recall: 93.33%, Specificity: 88.00%)
     * **Medicine & Biomedical ($N=100$)**: 96.00% Accuracy, 97.26% F1 (Recall: 94.67%, Specificity: 100.00%)
     * **Natural Sciences ($N=100$)**: 95.00% Accuracy, 96.60% F1 (Recall: 94.67%, Specificity: 96.00%)
     * **Humanities & Social Sciences ($N=100$)**: 94.00% Accuracy, 96.00% F1 (Recall: 96.00%, Specificity: 88.00%)
     * **Aggregate Holdout Performance ($N=400$)**: **94.25% Accuracy** (95% CI: [91.52%, 96.14%]), **96.11% F1-Score** (Precision CI: [95.12%, 98.83%], Recall CI: [91.51%, 96.69%], Specificity CI: [86.25%, 96.57%]), and **92.55% Macro-F1**.
   - *Explicit Separation of Benchmark Roles*:
     * **Accepted Paper V1.0 Camera-Ready (Historical)**: 90.33% Accuracy, 94.15% F1, $\text{TP}=467, \text{TN}=75, \text{FP}=25, \text{FN}=33$ ($N=600$, 100 CS seeds; archival freeze Aug 17, 2026).
     * **Diagnostic Benchmark V2.0**: 94.50% Accuracy, 96.64% F1, $\text{TP}=474, \text{TN}=93, \text{FP}=7, \text{FN}=26$ ($N=600$, same 100 CS seeds; diagnostic evaluation after repairing 24 no-ops).
     * **Independent Multidisciplinary Holdout**: 94.25% Accuracy, 96.11% F1, $\text{TP}=284, \text{TN}=93, \text{FP}=7, \text{FN}=16$ ($N=400$, 100 disjoint multidisciplinary seeds; cross-domain validation).
   - *Honest Statement of Ground-Truth Limitations*:
     * The holdout evaluates **controlled programmatic synthetic perturbations** (donor author swapping, donor venue swapping, year shifts, donor DOIs) anchored on real Crossref publications, rather than naturally occurring, open-domain LLM hallucinations.
     * All seed papers are indexed in Crossref; performance on non-indexed gray literature or non-English corpora remains untested.
     * These holdout results do not replace or alter the historical camera-ready conference paper results, nor do they establish empirical superiority over external systems such as CiteCheck.

#### 2. Completed Evidence Supporting Response
- Multi-source retriever implementation in `backend/app/services/multi_source_retriever.py`.
- Internal DOI existence baseline results verified directly in `datasets/citation_verification/baseline_results.csv` ($\text{Recall} = 40.00\%$, $\text{FN}=300$).
- Published CiteCheck system architecture and benchmark details (*Khajavi et al., 2025*, arXiv:2502.13322).
- Detailed CiteCheck feasibility and protocol analysis documented in `CITECHECK_COMPARISON_REPORT.md`.
- Independent Multidisciplinary Holdout dataset in `datasets/citation_verification/independent_holdout/independent_holdout_dataset.csv`.
- Holdout evaluation predictions and summary in `holdout_detailed_results.csv` and `holdout_summary.json`.
- Complete scientific audit report in `datasets/citation_verification/independent_holdout/FINAL_INDEPENDENT_AUDIT.md`.
- Content-addressed reproducible API cache in `reproducible_api_cache_holdout.json`.

#### 3. Honest Statement of Remaining Limitations
- No direct experimental data from running the CiteCheck codebase on our benchmarks exists in the repository.
- Controlled synthetic perturbations evaluate single-field and multi-field bibliographic corruption models, but do not reproduce the full unconstrained distribution of conversational hallucinations generated by large language models.
- Head-to-head empirical comparison on a shared, frozen, multi-disciplinary benchmark under standardized multi-system execution remains future work.

#### 4. Actionable Manuscript Changes Needed
- Update Section II ("Related Work") to include an architectural comparison contrasting CiteGuard's deterministic multi-source consensus pipeline with CiteCheck's published LLM-in-the-loop verifier, citing Khajavi et al. (2025).
- Discuss the single-source DOI existence ablation ($\text{Recall} = 40.00\%$) in Section V-B to motivate granular field-level verification.
- Add Section V-F ("Independent Multidisciplinary Generalization") presenting evaluation results across Computer Science, Medicine, Natural Sciences, and Humanities/Social Sciences ($N=400$).
- Explicitly disclose the programmatic synthetic perturbation methodology and acknowledge the boundary between controlled stress tests and unconstrained human-prompted hallucinations.

---

## Reconciled Performance Summary Table

For convenience, the complete performance profile across all configurations and benchmark tiers is summarized below:

$$\begin{array}{lcccc|cccc}
\hline
\textbf{Evaluation Tier / Configuration} & \textbf{TP} & \textbf{FN} & \textbf{FP} & \textbf{TN} & \textbf{Accuracy (95\% CI)} & \textbf{Balanced Acc} & \textbf{Specificity} & \textbf{F1 (95\% CI)} \\
\hline
\textbf{Accepted Camera-Ready (V1.0 Historical)} & & & & & & & & \\
\quad \text{Current CiteGuard (Baseline)} & 403 & 97 & 25 & 75 & 79.67\% & 80.20\% & 75.00\% & 86.85\% \\
\quad \text{CiteGuard + Author Fix} & 461 & 39 & 25 & 75 & 89.33\% & 83.60\% & 75.00\% & 93.51\% \\
\quad \text{CiteGuard + Venue Fix} & 409 & 91 & 25 & 75 & 80.67\% & 80.80\% & 75.00\% & 87.58\% \\
\quad \textbf{CiteGuard + Author + Venue Fix} & \mathbf{467} & \mathbf{33} & \mathbf{25} & \mathbf{75} & \mathbf{90.33\%} & \mathbf{84.20\%} & \mathbf{75.00\%} & \mathbf{94.15\%} \\
\hline
\textbf{Modern Committed Pipeline (V1.0 Baseline)} & & & & & & & & \\
\quad \text{CiteGuard + Author + Venue Fix} & 452 & 48 & 7 & 93 & 90.83\%\ [88.26\%, 92.89\%] & 91.70\% & 93.00\% & 94.26\%\ [92.67\%, 95.74\%] \\
\hline
\textbf{Modern Pipeline (Benchmark V2.0 Correction)} & & & & & & & & \\
\quad \text{Current CiteGuard} & 350 & 150 & 7 & 93 & 73.83\%\ [70.17\%, 77.19\%] & 81.50\% & 93.00\% & 81.68\%\ [78.69\%, 84.40\%] \\
\quad \text{CiteGuard + Author Fix} & 441 & 59 & 7 & 93 & 89.00\%\ [86.24\%, 91.26\%] & 90.60\% & 93.00\% & 93.04\%\ [91.29\%, 94.68\%] \\
\quad \text{CiteGuard + Venue Fix} & 383 & 117 & 7 & 93 & 79.33\%\ [75.91\%, 82.38\%] & 84.80\% & 93.00\% & 86.07\%\ [83.59\%, 88.46\%] \\
\quad \textbf{CiteGuard + Author + Venue Fix} & \mathbf{474} & \mathbf{26} & \mathbf{7} & \mathbf{93} & \mathbf{94.50\%}\ [92.38\%, 96.06\%] & \mathbf{93.90\%} & \mathbf{93.00\%} & \mathbf{96.64\%}\ [95.46\%, 97.73\%] \\
\hline
\textbf{Independent Multidisciplinary Holdout (N=400, Disjoint Seeds)} & & & & & & & & \\
\quad \text{Current CiteGuard (Baseline)} & 234 & 66 & 6 & 94 & 82.00\%\ [77.94\%, 85.45\%] & 86.00\% & 94.00\% & 86.67\% \\
\quad \text{CiteGuard + Author Fix} & 279 & 21 & 7 & 93 & 93.00\%\ [90.07\%, 95.11\%] & 93.00\% & 93.00\% & 95.22\% \\
\quad \text{CiteGuard + Venue Fix} & 239 & 61 & 6 & 94 & 83.25\%\ [79.28\%, 86.59\%] & 86.83\% & 94.00\% & 87.71\% \\
\quad \textbf{CiteGuard + Author + Venue Fix} & \mathbf{284} & \mathbf{16} & \mathbf{7} & \mathbf{93} & \mathbf{94.25\%}\ [91.52\%, 96.14\%] & \mathbf{93.83\%} & \mathbf{93.00\%} & \mathbf{96.11\%}\ [95.12\%, 98.83\%] \\
\hline
\end{array}$$

---

## Conclusion

This final scientific review confirms that CiteGuard's performance gains were empirically verified on the specified controlled benchmark using frozen repository artifacts. By clearly distinguishing archival camera-ready figures from diagnostic corrections, resolving label noise, and transparently acknowledging algorithmic limitations, this response provides a rigorous, professional, and scientifically defensible accounting to the reviewers and program committee.
