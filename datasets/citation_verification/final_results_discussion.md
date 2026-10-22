VI. RESULTS AND DISCUSSION

A. Overall Performance

The CiteGuard framework was evaluated on 600 citation instances, comprising 500 hallucinated citations and 100 valid citations. To eliminate variations caused by changes in external scholarly APIs, responses retrieved from Crossref, OpenAlex, and Semantic Scholar were frozen in an offline cache. All configurations therefore used identical retrieval evidence during evaluation. Hallucinated citations were treated as the positive class because the primary objective of CiteGuard is to detect fabricated or corrupted scholarly references.

The baseline CiteGuard configuration achieved an accuracy of 79.67%, precision of 94.16%, recall of 80.60%, and F1-score of 86.85%. Incorporating author validation increased the F1-score to 93.51%, while venue validation alone increased the F1-score to 87.58%. The combined author and venue configuration achieved the best performance, with 90.33% accuracy, 94.92% precision, 93.40% recall, and 94.15% F1-score.

The combined configuration therefore improved the F1-score by 7.30 percentage points compared with the baseline. Recall increased by 12.80 percentage points, from 80.60% to 93.40%, while precision remained above 94%. This indicates that the targeted metadata validation primarily improved the detection of hallucinated citations without substantially degrading precision.

B. Ablation Analysis

To determine the contribution of individual metadata validation components, four CiteGuard configurations were evaluated using identical cached retrieval results. The baseline configuration produced 97 false negatives, corresponding to hallucinated citations that were incorrectly accepted as valid. Adding author validation reduced the false negatives to 39, correcting 58 missed hallucinations. Venue validation alone reduced the false negatives to 91, correcting six cases. When both modifications were enabled, false negatives decreased to 33, corresponding to a reduction of 64 missed hallucinations from the baseline.

The combined author and venue configuration therefore reduced missed hallucinations by 65.98%, from 97 to 33 cases. Author validation provided the dominant improvement, while venue validation contributed an additional complementary reduction.

C. Error Analysis

The initial error analysis identified metadata inconsistency as a major source of citation verification errors. In particular, the original pipeline calculated author similarity but did not incorporate the resulting author consistency into the final citation-validity decision. Consequently, citations containing a correct title, year, and DOI but incorrect author information could still be accepted.

The author validation modification addressed this issue by requiring the existing author similarity threshold to be satisfied when author information was available. This modification corrected 58 of the original 97 missed hallucinations.

A second issue was identified in venue verification. The original venue similarity implementation permitted substring matches to receive a high similarity score. The venue modification removed this permissive shortcut and used the existing token-overlap calculation instead. Although its individual impact was smaller than that of author validation, the venue modification corrected six additional missed hallucinations.

The remaining errors indicate that metadata validation alone cannot completely resolve citation verification when the correct scholarly record is not retrieved or when multiple candidate records have similar metadata. In particular, 33 hallucinated citations remained incorrectly accepted by the combined configuration, while 25 valid citations were incorrectly rejected.

D. Limitations

Although the targeted metadata validation fixes substantially improved hallucination detection, 33 hallucinated citations remained incorrectly accepted by the combined configuration. In addition, 25 valid citations were incorrectly rejected across the evaluated configurations. These remaining errors indicate that further improvements require more robust retrieval and candidate-disambiguation mechanisms, particularly for generic titles, ambiguous metadata, and cases where external scholarly services return incomplete or competing records.

TABLE I
OVERALL HALLUCINATION DETECTION PERFORMANCE

| Configuration | Accuracy (%) | Precision (%) | Recall (%) | F1-score (%) |
|---------------|--------------|---------------|------------|--------------|
| Current CiteGuard | 79.67 | 94.16 | 80.60 | 86.85 |
| CiteGuard + Author Fix | 89.33 | 94.86 | 92.20 | 93.51 |
| CiteGuard + Venue Fix | 80.67 | 94.24 | 81.80 | 87.58 |
| CiteGuard + Author + Venue Fix | 90.33 | 94.92 | 93.40 | 94.15 |

TABLE II
CONFUSION MATRICES FOR TARGETED CITEGUARD CONFIGURATIONS

| Configuration | TP | FN | FP | TN |
|---------------|----|----|----|----|
| Current CiteGuard | 403 | 97 | 25 | 75 |
| CiteGuard + Author Fix | 461 | 39 | 25 | 75 |
| CiteGuard + Venue Fix | 409 | 91 | 25 | 75 |
| CiteGuard + Author + Venue Fix | 467 | 33 | 25 | 75 |

*Here, TP denotes hallucinated citations correctly detected, FN denotes hallucinated citations incorrectly accepted as valid, FP denotes valid citations incorrectly rejected, and TN denotes valid citations correctly accepted.*

![Confusion Matrices](C:/Users/A S Nemitha/.gemini/antigravity/brain/3ab87ce3-5934-4223-bde7-8cd19eb0180c/final_confusion_matrices.png)
![False Negative Reduction](C:/Users/A S Nemitha/.gemini/antigravity/brain/3ab87ce3-5934-4223-bde7-8cd19eb0180c/final_fn_reduction.png)
![Hallucination F1](C:/Users/A S Nemitha/.gemini/antigravity/brain/3ab87ce3-5934-4223-bde7-8cd19eb0180c/final_hallucination_f1.png)
![Ablation Performance](C:/Users/A S Nemitha/.gemini/antigravity/brain/3ab87ce3-5934-4223-bde7-8cd19eb0180c/final_ablation_performance.png)

---
*All configurations were evaluated on the same 600 citation instances using a frozen offline snapshot of retrieval responses from Crossref, OpenAlex, and Semantic Scholar. Hallucinated citations were treated as the positive class. No benchmark instances, ground-truth labels, or decision thresholds were modified during evaluation.*
