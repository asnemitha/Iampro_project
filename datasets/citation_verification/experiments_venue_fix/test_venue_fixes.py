"""
test_venue_fixes.py
===================
Experimental diagnostic test suite validating the controlled Venue Fix.
Tests:
1. Subset-name false matches (Baseline allows them; Venue Fix correctly rejects them).
2. Legitimate canonical venue aliases (NeurIPS, ICML, CVPR, ICLR).
3. Punctuation, casing, and standard prefix normalization.
4. Full venue-name variants.
"""

import sys
import unittest
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).resolve().parents[3] / "backend"
sys.path.insert(0, str(backend_dir))

from app.services.similarity_service import (
    compare_venues,
    normalize_venue_name,
    VENUE_ALIASES,
)


class TestVenueFixes(unittest.TestCase):

    def test_subset_false_matches_separated_by_fix(self):
        """
        Verify that Baseline allows subset venue shortcuts,
        while Venue Fix correctly catches the mismatch.
        """
        subset_pairs = [
            ("Deep Learning", "Mathematical Foundations for Deep Learning"),
            ("Machine Learning with Applications", "Machine Learning"),
            ("Artificial Intelligence", "Artificial Intelligence and Digital Development"),
        ]
        
        for claimed, actual in subset_pairs:
            # Baseline allows via substring containment or token_set_ratio
            match_base, score_base = compare_venues(claimed, actual, use_venue_fix=False)
            self.assertTrue(
                match_base,
                f"Baseline should have matched subset pair '{claimed}' vs '{actual}'"
            )
            
            # Venue Fix removes shortcut and applies token_sort_ratio < 70
            match_fix, score_fix = compare_venues(claimed, actual, use_venue_fix=True)
            self.assertFalse(
                match_fix,
                f"Venue Fix should have REJECTED subset mutation '{claimed}' vs '{actual}' (got score {score_fix})"
            )
            self.assertLess(score_fix, 70.0)

    def test_nature_and_science_sister_journal_distinction(self):
        """
        Verify that Nature/Science do NOT automatically match distinct sister journals
        such as Nature Chemistry, Nature Machine Intelligence, or Science Advances.
        """
        sister_pairs = [
            ("Nature", "Nature Machine Intelligence"),
            ("Nature", "Nature Chemistry"),
            ("Nature", "Nature Communications"),
            ("Science", "Science Advances"),
            ("Science", "Cognitive Science"),
        ]
        
        for v1, v2 in sister_pairs:
            # Under Venue Fix, sister journals must be rejected
            m_fix, s_fix = compare_venues(v1, v2, use_venue_fix=True)
            self.assertFalse(
                m_fix,
                f"Venue Fix must reject sister journal pair: '{v1}' vs '{v2}' (got score {s_fix})"
            )
            self.assertLess(s_fix, 70.0)

        # Confirm that exact Nature matches still succeed
        m_exact, s_exact = compare_venues("Nature", "Nature", use_venue_fix=True)
        self.assertTrue(m_exact, "Exact Nature match must succeed")
        self.assertEqual(s_exact, 100.0)

        m_sci, s_sci = compare_venues("Science", "Science", use_venue_fix=True)
        self.assertTrue(m_sci, "Exact Science match must succeed")
        self.assertEqual(s_sci, 100.0)

    def test_legitimate_venue_aliases(self):
        """
        Verify that canonical academic aliases match under BOTH baseline and venue fix.
        """
        alias_pairs = [
            ("NeurIPS", "Advances in Neural Information Processing Systems"),
            ("NIPS", "Advances in Neural Information Processing Systems"),
            ("ICML", "International Conference on Machine Learning"),
            ("CVPR", "IEEE Conference on Computer Vision and Pattern Recognition"),
            ("ICLR", "International Conference on Learning Representations"),
            ("AAAI", "AAAI Conference on Artificial Intelligence"),
        ]
        
        for alias, full_name in alias_pairs:
            # Both must match with high confidence
            m_base, s_base = compare_venues(alias, full_name, use_venue_fix=False)
            m_fix, s_fix = compare_venues(alias, full_name, use_venue_fix=True)
            
            self.assertTrue(m_base, f"Baseline failed alias: {alias}")
            self.assertTrue(m_fix, f"Venue Fix failed alias: {alias}")
            self.assertGreaterEqual(s_fix, 90.0)

    def test_normalization_and_prefixes(self):
        """
        Verify that punctuation, casing, and standard prefixes (Proceedings of, etc.)
        are normalized under both configurations.
        """
        prefix_pairs = [
            ("Proceedings of the International Conference on Machine Learning", "International Conference on Machine Learning"),
            ("Journal of Machine Learning Research", "journal of machine learning research."),
            ("Nature Chemistry", "Nature chemistry: vol. 3"),
            ("Transactions on Pattern Analysis and Machine Intelligence", "Pattern Analysis and Machine Intelligence"),
        ]
        
        for v1, v2 in prefix_pairs:
            m_base, s_base = compare_venues(v1, v2, use_venue_fix=False)
            m_fix, s_fix = compare_venues(v1, v2, use_venue_fix=True)
            
            self.assertTrue(m_base, f"Baseline failed prefix pair: {v1} vs {v2}")
            self.assertTrue(m_fix, f"Venue Fix failed prefix pair: {v1} vs {v2}")
            self.assertGreaterEqual(s_fix, 90.0)

    def test_threshold_parameter_propagation_in_compare_venues(self):
        """
        REGRESSION TEST: Verify threshold experiment passes each threshold into
        the exact comparison function. Fails if threshold changes are ignored.
        """
        # Pair that scores exactly 64.0 under token_sort_ratio
        v1 = "Machine Learning with Applications"
        v2 = "Machine Learning"

        # At threshold=60: 64.0 >= 60 -> True
        match_60, score_60 = compare_venues(v1, v2, use_venue_fix=True, threshold=60)
        self.assertTrue(match_60, f"Expected match at threshold=60 (score={score_60})")

        # At default threshold=70: 64.0 < 70 -> False
        match_70, score_70 = compare_venues(v1, v2, use_venue_fix=True, threshold=70)
        self.assertFalse(match_70, f"Expected reject at threshold=70 (score={score_70})")

        # At threshold=80: 64.0 < 80 -> False
        match_80, score_80 = compare_venues(v1, v2, use_venue_fix=True, threshold=80)
        self.assertFalse(match_80, f"Expected reject at threshold=80 (score={score_80})")

        # Critical assertion: If threshold parameter was ignored and hardcoded to 70 or not used,
        # match_60 would be False (identical to match_70), and this assertion FAILS.
        self.assertNotEqual(
            match_60,
            match_70,
            "CRITICAL FAILURE: Threshold parameter is ignored in compare_venues!"
        )

    def test_pipeline_threshold_parameter_propagation(self):
        """
        REGRESSION TEST: Verify verify_response propagates venue_threshold into
        the evaluation pipeline. Fails if threshold changes are ignored by verify_response.
        """
        from unittest.mock import patch
        from app.services import verification_pipeline

        # Citation with venue pair scoring 64.0 (Machine Learning with Applications vs Machine Learning)
        citation_text = (
            "[1] Real Paper Title\n"
            "Authors: John Doe\n"
            "Year: 2022\n"
            "Venue: Machine Learning with Applications\n"
            "DOI: 10.1000/182\n"
        )

        mock_paper = {
            "title": "Real Paper Title",
            "authors": ["John Doe"],
            "year": 2022,
            "venue": "Machine Learning",
            "doi": "10.1000/182",
            "source": "Crossref"
        }

        # Mock retrieval to return this paper
        with patch.object(verification_pipeline, "verify_doi", return_value=mock_paper), \
             patch.object(verification_pipeline, "retrieve_candidates", return_value=[mock_paper]):
            
            # Evaluate at threshold 60 (score 64 >= 60 -> venue matches, accurate)
            res_60 = verification_pipeline.verify_response(
                citation_text,
                use_author_fix=True,
                use_venue_fix=True,
                venue_threshold=60.0
            )
            pred_60 = 0 if res_60 and res_60[0].get("citation_accurate") else 1

            # Evaluate at threshold 70 (score 64 < 70 -> venue mismatch, hallucinated)
            res_70 = verification_pipeline.verify_response(
                citation_text,
                use_author_fix=True,
                use_venue_fix=True,
                venue_threshold=70.0
            )
            pred_70 = 0 if res_70 and res_70[0].get("citation_accurate") else 1

            self.assertEqual(pred_60, 0, "At T=60 (64 >= 60), venue should match and citation be accurate")
            self.assertEqual(pred_70, 1, "At T=70 (64 < 70), venue should mismatch and citation be flagged")

            # Critical assertion: If pipeline ignored venue_threshold, both predictions would be identical!
            self.assertNotEqual(
                pred_60,
                pred_70,
                "CRITICAL FAILURE: Pipeline verify_response ignored venue_threshold parameter!"
            )


if __name__ == "__main__":
    unittest.main()

