"""
test_venue_generalization.py
============================
Independent Venue Matching Generalization Test Set
Sourced from scholarly indexing variations (IEEE, ACM, Springer, Elsevier, arXiv).
Evaluates False Acceptance Rate (FAR) and False Rejection Rate (FRR)
for Baseline (Current CiteGuard) vs. Venue Fix.

Ground Truth Definition:
- is_same_venue = True: Real legitimate variant, abbreviation, or alias.
- is_same_venue = False: Different venue, subset manipulation, or incorrect substitution.
"""

import sys
import json
from pathlib import Path

# Add backend to path
base_dir = Path(__file__).resolve().parents[4]
backend_dir = base_dir / "backend"
sys.path.insert(0, str(backend_dir))

from app.services.similarity_service import compare_venues

# Sourced benchmark independent test cases (40 curated pairs)
GENERALIZATION_TEST_SET = [
    # -------------------------------------------------------------
    # 20 POSITIVE PAIRS (True Matches - Should be ACCEPTED)
    # -------------------------------------------------------------
    {"v1": "NeurIPS", "v2": "Advances in Neural Information Processing Systems", "is_same_venue": True, "category": "acronym_expansion"},
    {"v1": "ICML", "v2": "International Conference on Machine Learning", "is_same_venue": True, "category": "acronym_expansion"},
    {"v1": "CVPR", "v2": "IEEE/CVF Conference on Computer Vision and Pattern Recognition", "is_same_venue": True, "category": "acronym_expansion"},
    {"v1": "ICLR", "v2": "International Conference on Learning Representations", "is_same_venue": True, "category": "acronym_expansion"},
    {"v1": "AAAI", "v2": "AAAI Conference on Artificial Intelligence", "is_same_venue": True, "category": "acronym_expansion"},
    {"v1": "EMNLP", "v2": "Empirical Methods in Natural Language Processing", "is_same_venue": True, "category": "acronym_expansion"},
    {"v1": "ACL", "v2": "Association for Computational Linguistics", "is_same_venue": True, "category": "acronym_expansion"},
    {"v1": "Journal of Machine Learning Research", "v2": "journal of machine learning research.", "is_same_venue": True, "category": "case_punctuation"},
    {"v1": "Nature Chemistry: Volume 3", "v2": "Nature Chemistry", "is_same_venue": True, "category": "volume_prefix_normalization"},
    {"v1": "Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition", "v2": "IEEE Conference on Computer Vision and Pattern Recognition", "is_same_venue": True, "category": "proceedings_prefix"},
    {"v1": "Transactions on Pattern Analysis and Machine Intelligence", "v2": "IEEE Transactions on Pattern Analysis and Machine Intelligence", "is_same_venue": True, "category": "publisher_prefix"},
    {"v1": "arXiv preprint arXiv:2103.00020", "v2": "arXiv", "is_same_venue": True, "category": "arxiv_variant"},
    {"v1": "Cornell University Library (arXiv)", "v2": "arXiv:1706.03762", "is_same_venue": True, "category": "arxiv_variant"},
    {"v1": "Communications of the ACM", "v2": "CACM", "is_same_venue": True, "category": "acronym_expansion"},
    {"v1": "PNAS", "v2": "Proceedings of the National Academy of Sciences", "is_same_venue": True, "category": "acronym_expansion"},
    {"v1": "Artificial Intelligence", "v2": "Artificial Intelligence (AIJ)", "is_same_venue": True, "category": "acronym_parenthesis"},
    {"v1": "Machine Learning", "v2": "Machine Learning Journal", "is_same_venue": True, "category": "journal_suffix"},
    {"v1": "Data Mining and Knowledge Discovery", "v2": "Data mining and knowledge discovery", "is_same_venue": True, "category": "case_normalization"},
    {"v1": "ACM Transactions on Graphics", "v2": "Transactions on Graphics (TOG)", "is_same_venue": True, "category": "acronym_parenthesis"},
    {"v1": "IEEE Robotics and Automation Letters", "v2": "Robotics and Automation Letters", "is_same_venue": True, "category": "publisher_prefix"},

    # -------------------------------------------------------------
    # 20 NEGATIVE PAIRS (Different Venues - Should be REJECTED)
    # -------------------------------------------------------------
    {"v1": "Deep Learning", "v2": "Mathematical Foundations for Deep Learning", "is_same_venue": False, "category": "subset_broadening"},
    {"v1": "Machine Learning with Applications", "v2": "Machine Learning", "is_same_venue": False, "category": "distinct_spinoff_journal"},
    {"v1": "Nature", "v2": "Nature Machine Intelligence", "is_same_venue": False, "category": "distinct_sister_journal"},
    {"v1": "Nature", "v2": "Nature Chemistry", "is_same_venue": False, "category": "distinct_sister_journal"},
    {"v1": "Artificial Intelligence", "v2": "Artificial Intelligence and Digital Development", "is_same_venue": False, "category": "subset_broadening"},
    {"v1": "Computer Vision and Image Understanding", "v2": "Series in Computer Vision", "is_same_venue": False, "category": "book_series_vs_journal"},
    {"v1": "Natural Language Processing", "v2": "International Conference on Natural Language Processing and Knowledge Engineering", "is_same_venue": False, "category": "subset_broadening"},
    {"v1": "Deep Learning Pipeline", "v2": "Hands-on Deep Learning", "is_same_venue": False, "category": "distinct_book_title"},
    {"v1": "Machine Learning", "v2": "Fundamentals of Machine Learning", "is_same_venue": False, "category": "distinct_book_title"},
    {"v1": "ICML", "v2": "NeurIPS", "is_same_venue": False, "category": "different_top_conference"},
    {"v1": "CVPR", "v2": "ICCV", "is_same_venue": False, "category": "different_top_conference"},
    {"v1": "IEEE Transactions on Information Theory", "v2": "IEEE Transactions on Communications", "is_same_venue": False, "category": "different_ieee_transactions"},
    {"v1": "Journal of Artificial Intelligence Research", "v2": "Artificial Intelligence", "is_same_venue": False, "category": "different_competing_journal"},
    {"v1": "Bioinformatics", "v2": "Briefings in Bioinformatics", "is_same_venue": False, "category": "different_competing_journal"},
    {"v1": "IEEE Transactions on Neural Networks", "v2": "IEEE Transactions on Neural Networks and Learning Systems", "is_same_venue": False, "category": "successor_journal_different_scope"},
    {"v1": "Soft Computing and Machine Learning", "v2": "Machine Learning", "is_same_venue": False, "category": "subset_broadening"},
    {"v1": "Quantum Machine Learning", "v2": "Soft Computing and Machine Learning", "is_same_venue": False, "category": "distinct_topic_venue"},
    {"v1": "Building Scalable Deep Learning Pipelines on AWS", "v2": "Deep Learning", "is_same_venue": False, "category": "subset_broadening"},
    {"v1": "Automated Machine Learning for Business", "v2": "Machine Learning", "is_same_venue": False, "category": "subset_broadening"},
    {"v1": "Applications of Artificial Intelligence in Chemistry", "v2": "Artificial Intelligence", "is_same_venue": False, "category": "subset_broadening"}
]


def evaluate_generalization():
    print("=" * 80)
    print("INDEPENDENT VENUE GENERALIZATION EVALUATION (40 Scholarly Pairs)")
    print("=" * 80)

    # Counts
    base_tp = base_tn = base_fp = base_fn = 0
    fix_tp = fix_tn = fix_fp = fix_fn = 0

    detailed_results = []

    for item in GENERALIZATION_TEST_SET:
        v1, v2 = item["v1"], item["v2"]
        target = item["is_same_venue"]

        # Run Baseline (use_venue_fix=False)
        m_base, s_base = compare_venues(v1, v2, use_venue_fix=False)
        # Run Venue Fix (use_venue_fix=True)
        m_fix, s_fix = compare_venues(v1, v2, use_venue_fix=True)

        # Baseline confusion
        if target and m_base: base_tp += 1
        elif not target and not m_base: base_tn += 1
        elif not target and m_base: base_fp += 1
        elif target and not m_base: base_fn += 1

        # Venue Fix confusion
        if target and m_fix: fix_tp += 1
        elif not target and not m_fix: fix_tn += 1
        elif not target and m_fix: fix_fp += 1
        elif target and not m_fix: fix_fn += 1

        detailed_results.append({
            "v1": v1, "v2": v2, "target_match": target,
            "category": item["category"],
            "base_match": m_base, "base_score": s_base,
            "fix_match": m_fix, "fix_score": s_fix
        })

    # Metrics
    # FAR = FP / (FP + TN) -> rate of accepting different venues
    # FRR = FN / (FN + TP) -> rate of rejecting legitimate same venues
    base_far = (base_fp / (base_fp + base_tn)) * 100
    base_frr = (base_fn / (base_fn + base_tp)) * 100
    base_acc = ((base_tp + base_tn) / len(GENERALIZATION_TEST_SET)) * 100

    fix_far = (fix_fp / (fix_fp + fix_tn)) * 100
    fix_frr = (fix_fn / (fix_fn + fix_tp)) * 100
    fix_acc = ((fix_tp + fix_tn) / len(GENERALIZATION_TEST_SET)) * 100

    print(f"\nTotal Test Pairs: {len(GENERALIZATION_TEST_SET)} (20 Authentic Matches, 20 Fake/Different Venues)")
    print("-" * 80)
    print(f"{'Metric':<35} {'Baseline (Current CiteGuard)':<25} {'Experimental Venue Fix':<25}")
    print("-" * 80)
    print(f"{'Overall Accuracy':<35} {base_acc:.2f}%{'':<18} {fix_acc:.2f}%")
    print(f"{'False Acceptance Rate (FAR)':<35} {base_far:.2f}% (FP={base_fp}){'':<11} {fix_far:.2f}% (FP={fix_fp})")
    print(f"{'False Rejection Rate (FRR)':<35} {base_frr:.2f}% (FN={base_fn}){'':<12} {fix_frr:.2f}% (FN={fix_fn})")
    print(f"{'Correct Authentic Matches (TP)':<35} {base_tp}/20{'':<20} {fix_tp}/20")
    print(f"{'Correct Distinctions (TN)':<35} {base_tn}/20{'':<20} {fix_tn}/20")
    print("-" * 80)

    # Save results
    val_dir = base_dir / "datasets" / "citation_verification" / "experiments_venue_fix" / "validation"
    val_dir.mkdir(parents=True, exist_ok=True)
    with open(val_dir / "generalization_evaluation.json", "w", encoding="utf-8") as f:
        json.dump({
            "summary": {
                "baseline": {"accuracy": base_acc, "far": base_far, "frr": base_frr, "tp": base_tp, "tn": base_tn, "fp": base_fp, "fn": base_fn},
                "venue_fix": {"accuracy": fix_acc, "far": fix_far, "frr": fix_frr, "tp": fix_tp, "tn": fix_tn, "fp": fix_fp, "fn": fix_fn}
            },
            "detailed_pairs": detailed_results
        }, f, indent=2)

    print(f"\n[OK] Saved independent generalization evaluation to: {val_dir / 'generalization_evaluation.json'}")


if __name__ == "__main__":
    evaluate_generalization()
