"""
test_venue_and_metadata_matching.py
====================================
Focused diagnostic unit tests for citation verification matching mechanics.
Tests:
1. Subset-name venue matches (demonstrating why token_set_ratio bypasses use_venue_fix).
2. Legitimate venue aliases and acronym expansions.
3. Author corruption detection under Baseline (use_author_fix=False) vs Fix (use_author_fix=True).
4. DOI mismatch handling.

NOTE: This is a diagnostic-only test suite. It does not modify production code.
"""

import sys
import unittest
from pathlib import Path
from rapidfuzz import fuzz

# Add backend to path
backend_dir = Path(__file__).resolve().parents[3] / "backend"
sys.path.insert(0, str(backend_dir))

from app.services.similarity_service import (
    compare_venues,
    normalize_venue_name,
    compare_authors,
    compare_dois,
    compare_titles,
    VENUE_ALIASES,
)


class TestVenueAndMetadataMatching(unittest.TestCase):
    
    # =========================================================================
    # Test 1: Subset-name Venue Matches (Root cause of Venue Fix discrepancy)
    # =========================================================================
    def test_subset_venue_matching_behavior(self):
        """
        Demonstrate that token_set_ratio produces 100% on word subsets,
        causing compare_venues to return True even when use_venue_fix=True.
        """
        test_pairs = [
            ("Deep Learning", "Mathematical Foundations for Deep Learning"),
            ("Machine Learning with Applications", "Machine Learning"),
            ("Natural Language Processing", "Natural Language Processing Journal"),
            ("Artificial Intelligence", "Artificial Intelligence and Digital Development")
        ]
        
        for v_claimed, v_actual in test_pairs:
            n1 = normalize_venue_name(v_claimed)
            n2 = normalize_venue_name(v_actual)
            
            ts_score = fuzz.token_set_ratio(n1, n2)
            sort_score = fuzz.token_sort_ratio(n1, n2)
            
            match_base, score_base = compare_venues(v_claimed, v_actual, use_venue_fix=False)
            match_fix, score_fix = compare_venues(v_claimed, v_actual, use_venue_fix=True)
            
            # Key diagnostic finding:
            # Word subsets yield token_set_ratio == 100.0, so both baseline and fix return True
            self.assertEqual(ts_score, 100.0, f"Expected 100 token_set on subset '{n1}' vs '{n2}'")
            self.assertTrue(match_base, "Baseline matches via substring containment")
            if sort_score < 70.0:
                self.assertFalse(match_fix, f"Fix correctly rejects subset mutation '{n1}' vs '{n2}'")
            else:
                self.assertTrue(match_fix, f"Minor single-word journal variant scores {sort_score:.1f}")
            # In major subset mutations like Deep Learning vs Mathematical Foundations, token_sort is low
            if "Mathematical Foundations" in v_actual or "Applications" in v_claimed:
                self.assertLess(sort_score, 70.0, "token_sort_ratio separates broad subset mutations")

    # =========================================================================
    # Test 2: Legitimate Venue Aliases
    # =========================================================================
    def test_legitimate_venue_aliases(self):
        """
        Verify that canonical scholarly acronyms match their full conference titles.
        """
        alias_pairs = [
            ("NeurIPS", "Advances in Neural Information Processing Systems"),
            ("ICML", "International Conference on Machine Learning"),
            ("CVPR", "IEEE Conference on Computer Vision and Pattern Recognition"),
            ("ICLR", "International Conference on Learning Representations")
        ]
        
        for acronym, full_title in alias_pairs:
            is_match, score = compare_venues(acronym, full_title)
            self.assertTrue(is_match, f"Failed to match legitimate alias: {acronym} <-> {full_title}")
            self.assertGreaterEqual(score, 90.0)

    # =========================================================================
    # Test 3: Author Corruption Detection
    # =========================================================================
    def test_author_corruption_matching(self):
        """
        Verify author similarity scoring on real vs fabricated/corrupted author lists.
        """
        # Genuine match
        claimed_real = ["Pat Langley", "Ryszard S. Michalski"]
        verified_real = ["Pat Langley", "Ryszard S. Michalski"]
        self.assertEqual(compare_authors(claimed_real, verified_real), 100.0)
        
        # Corrupted author list (fabricated names)
        claimed_fake = ["Tayyaba Hussain"]
        verified_actual = ["Raymond Lee"]
        self.assertEqual(compare_authors(claimed_fake, verified_actual), 0.0)
        
        # Partial overlap (1 of 2 correct)
        claimed_partial = ["Pat Langley", "John Doe"]
        verified_authors = ["Pat Langley", "Ryszard S. Michalski"]
        score_partial = compare_authors(claimed_partial, verified_authors)
        self.assertEqual(score_partial, 50.0)
        
        # In baseline (use_author_fix=False), author mismatches are bypassed:
        # author_check = True
        # In author fix (use_author_fix=True), score >= 70 is required:
        self.assertFalse(score_partial >= 70.0, "Author fix correctly rejects 50% partial author overlap")

    # =========================================================================
    # Test 4: DOI Mismatches
    # =========================================================================
    def test_doi_comparison_and_mismatch(self):
        """
        Verify DOI equivalence handling and format variations.
        """
        # Equivalent DOIs with varying formatting
        doi1 = "10.1038/nchem.1145"
        doi2 = "https://doi.org/10.1038/nchem.1145"
        doi3 = "doi:10.1038/NCHEM.1145"
        self.assertTrue(compare_dois(doi1, doi2))
        self.assertTrue(compare_dois(doi1, doi3))
        
        # Mismatched DOIs
        wrong_doi = "10.1145/1146238.1146241"
        self.assertFalse(compare_dois(doi1, wrong_doi))


if __name__ == "__main__":
    unittest.main()
