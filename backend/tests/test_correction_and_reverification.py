import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "backend"))

from app.services.correction_service import (
    correct_and_reverify_response,
    build_replacement_citation,
    build_qualified_unverified_citation,
    search_replacement_paper,
)
from app.services.claim_verification_service import (
    extract_claim_for_citation,
    verify_claim_support,
)
from app.services.verification_pipeline import verify_response


# ==============================================================================
# SCENARIO 1: All citations are valid and no correction is needed.
# ==============================================================================
def test_01_all_citations_valid_no_correction():
    text = """1. Deep Residual Learning for Image Recognition
Authors: Kaiming He, Xiangyu Zhang, Shaoqing Ren, Jian Sun
Year: 2016
Venue: CVPR
DOI: 10.1109/CVPR.2016.90"""

    mock_result = [{
        "citation": text,
        "paper_exists": True,
        "citation_accurate": True,
        "hallucination_type": "Valid Citation",
        "metadata_errors": [],
        "matched_title": "Deep Residual Learning for Image Recognition",
        "matched_authors": ["Kaiming He", "Xiangyu Zhang", "Shaoqing Ren", "Jian Sun"],
        "matched_year": 2016,
        "matched_venue": "CVPR",
        "matched_doi": "10.1109/CVPR.2016.90",
        "matched_abstract": "Deep residual networks use residual learning framework to ease training of deep neural networks.",
        "hallucination_score": 0,
        "confidence": "Verified Citation",
    }]

    with patch("app.services.correction_service.verify_response", return_value=mock_result):
        res = correct_and_reverify_response(text, max_iterations=2)

        assert res["verification_summary"]["final_status"] == "verified"
        assert res["verification_summary"]["unresolved_count"] == 0
        assert res["verification_summary"]["verified_count"] == 1
        assert len(res["applied_corrections"]) == 0
        assert res["final_response"] == text


# ==============================================================================
# SCENARIO 2: A citation has an incorrect title or author.
# ==============================================================================
def test_02_citation_has_incorrect_author_corrected_and_reverified():
    flawed_text = """1. Attention Is All You Need
Authors: Geoffrey Hinton, Yann LeCun
Year: 2017
Venue: NeurIPS
DOI: 10.48550/arXiv.1706.03762"""

    flawed_result = [{
        "citation": flawed_text,
        "paper_exists": True,
        "citation_accurate": False,
        "hallucination_type": "Metadata Hallucination",
        "metadata_errors": ["Author mismatch"],
        "matched_title": "Attention Is All You Need",
        "matched_authors": ["Ashish Vaswani", "Noam Shazeer", "Niki Parmar", "Jakob Uszkoreit"],
        "matched_year": 2017,
        "matched_venue": "NeurIPS",
        "matched_doi": "10.48550/arXiv.1706.03762",
        "matched_abstract": "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks.",
        "hallucination_score": 35,
    }]

    corrected_result = [{
        "citation": """1. Attention Is All You Need
Authors: Ashish Vaswani, Noam Shazeer, Niki Parmar, Jakob Uszkoreit
Year: 2017
Venue: NeurIPS
DOI: 10.48550/arXiv.1706.03762""",
        "paper_exists": True,
        "citation_accurate": True,
        "hallucination_type": "Valid Citation",
        "metadata_errors": [],
        "matched_title": "Attention Is All You Need",
        "matched_authors": ["Ashish Vaswani", "Noam Shazeer", "Niki Parmar", "Jakob Uszkoreit"],
        "matched_year": 2017,
        "matched_venue": "NeurIPS",
        "matched_doi": "10.48550/arXiv.1706.03762",
        "matched_abstract": "The dominant sequence transduction models...",
        "hallucination_score": 0,
    }]

    # Iteration 1 returns flawed_result; Iteration 2 (after replacement) returns corrected_result
    with patch("app.services.correction_service.verify_response", side_effect=[flawed_result, corrected_result]):
        res = correct_and_reverify_response(flawed_text, max_iterations=2)

        assert len(res["applied_corrections"]) == 1
        assert res["applied_corrections"][0]["verified_in_next_step"] is True
        assert res["verification_summary"]["final_status"] == "verified"
        assert res["verification_summary"]["corrected_and_verified_count"] == 1
        assert "Ashish Vaswani" in res["final_response"]
        assert "Geoffrey Hinton" not in res["final_response"]


# ==============================================================================
# SCENARIO 3: A DOI is invalid or points to a different paper.
# ==============================================================================
def test_03_invalid_doi_corrected_and_reverified():
    flawed_text = """1. Deep Residual Learning for Image Recognition
Authors: Kaiming He, Xiangyu Zhang, Shaoqing Ren, Jian Sun
Year: 2016
Venue: CVPR
DOI: 10.1038/nature12345"""

    flawed_result = [{
        "citation": flawed_text,
        "paper_exists": True,
        "citation_accurate": False,
        "hallucination_type": "Metadata Hallucination",
        "metadata_errors": ["DOI mismatch"],
        "matched_title": "Deep Residual Learning for Image Recognition",
        "matched_authors": ["Kaiming He", "Xiangyu Zhang", "Shaoqing Ren", "Jian Sun"],
        "matched_year": 2016,
        "matched_venue": "CVPR",
        "matched_doi": "10.1109/CVPR.2016.90",
        "matched_abstract": "Deeper neural networks are more difficult to train.",
    }]

    corrected_result = [{
        "citation": """1. Deep Residual Learning for Image Recognition
Authors: Kaiming He, Xiangyu Zhang, Shaoqing Ren, Jian Sun
Year: 2016
Venue: CVPR
DOI: 10.1109/CVPR.2016.90""",
        "paper_exists": True,
        "citation_accurate": True,
        "hallucination_type": "Valid Citation",
        "metadata_errors": [],
        "matched_title": "Deep Residual Learning for Image Recognition",
        "matched_authors": ["Kaiming He", "Xiangyu Zhang", "Shaoqing Ren", "Jian Sun"],
        "matched_year": 2016,
        "matched_venue": "CVPR",
        "matched_doi": "10.1109/CVPR.2016.90",
        "matched_abstract": "Deeper neural networks are more difficult to train.",
    }]

    with patch("app.services.correction_service.verify_response", side_effect=[flawed_result, corrected_result]):
        res = correct_and_reverify_response(flawed_text, max_iterations=2)

        assert res["verification_summary"]["final_status"] == "verified"
        assert "10.1109/CVPR.2016.90" in res["final_response"]
        assert "10.1038/nature12345" not in res["final_response"]


# ==============================================================================
# SCENARIO 4: A citation cannot be found in available sources.
# ==============================================================================
def test_04_citation_not_found_transparently_qualified():
    fake_text = """1. Quantum Transformer Architectures for Graph Neural Networks
Authors: David Silver, Demis Hassabis
Year: 2022
Venue: IEEE TNNLS
DOI: 10.1109/TNNLS.2022.9876543"""

    fake_result = [{
        "citation": fake_text,
        "paper_exists": False,
        "citation_accurate": False,
        "hallucination_type": "Fabricated Citation",
        "metadata_errors": ["Paper could not be found in Crossref, Semantic Scholar or OpenAlex."],
        "matched_title": None,
        "matched_authors": [],
        "matched_year": None,
        "matched_venue": None,
        "matched_doi": None,
        "matched_abstract": None,
        "hallucination_score": 100,
    }]

    with patch("app.services.correction_service.verify_response", return_value=fake_result), \
         patch("app.services.correction_service.search_replacement_paper", return_value=None):
        res = correct_and_reverify_response(fake_text, max_iterations=2)

        # Must never be labeled fully verified
        assert res["verification_summary"]["final_status"] != "verified"
        assert res["verification_summary"]["unresolved_count"] >= 1
        assert ("UNVERIFIED REFERENCE" in res["final_response"] or "[Warning: Claim-to-source mismatch" in res["final_response"])


# ==============================================================================
# SCENARIO 5: A citation exists, but the associated claim is unsupported.
# ==============================================================================
def test_05_citation_exists_but_claim_unsupported():
    text = """Photosynthesis in marine algae generates high-temperature superconducting plasma.

1. Attention Is All You Need
Authors: Ashish Vaswani et al.
Year: 2017
Venue: NeurIPS
DOI: 10.48550/arXiv.1706.03762"""

    paper_record = {
        "paper_exists": True,
        "matched_title": "Attention Is All You Need",
        "matched_abstract": "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks.",
    }

    claim = extract_claim_for_citation(text, "1. Attention Is All You Need")
    claim_res = verify_claim_support(claim, paper_record)

    assert claim_res["status"] == "unsupported_claim"
    assert claim_res["supported"] is False
    assert "different subject" in claim_res["reason"].lower() or "different topic" in claim_res["reason"].lower()


# ==============================================================================
# SCENARIO 6: Fabricated citations are never substituted with unrelated papers.
# ==============================================================================
def test_06_fabricated_citation_never_substituted_with_unrelated_paper():
    fake_text = """1. Residual Skip Learning for Vision
Authors: John Doe
Year: 2015
Summary: Introduces skip connections to train deep residual networks up to 152 layers."""

    fake_result = [{
        "citation": fake_text,
        "paper_exists": False,
        "citation_accurate": False,
        "hallucination_type": "Fabricated Citation",
        "metadata_errors": ["Paper not found"],
        "matched_title": None,
        "matched_authors": [],
        "matched_year": None,
        "matched_venue": None,
        "matched_doi": None,
    }]

    genuine_unrelated_paper = {
        "title": "Deep Residual Learning for Image Recognition",
        "authors": ["Kaiming He", "Xiangyu Zhang", "Shaoqing Ren", "Jian Sun"],
        "year": 2016,
        "venue": "CVPR",
        "doi": "10.1109/CVPR.2016.90",
        "abstract": "Deeper neural networks are more difficult to train. We present a residual learning framework.",
    }

    with patch("app.services.correction_service.verify_response", return_value=fake_result), \
         patch("app.services.correction_service.search_replacement_paper", return_value=genuine_unrelated_paper):
        res = correct_and_reverify_response(fake_text, max_iterations=2)

        # Must NEVER substitute an unrelated paper to make a fabricated citation appear verified
        assert res["verification_summary"]["final_status"] != "verified"
        assert res["verification_summary"]["unresolved_count"] >= 1
        assert "Deep Residual Learning for Image Recognition" not in res["final_response"]
        assert "UNVERIFIED REFERENCE" in res["final_response"]


# ==============================================================================
# SCENARIO 7: No reliable replacement source is found.
# ==============================================================================
def test_07_no_reliable_replacement_source_found_never_fabricates():
    fake_text = """1. Hyper-Dimensional Quantum Telepathy via Neural Synapses
Authors: Alice Fake, Bob Imaginary
Year: 2024
Venue: Fictional Journal of Impossible Science"""

    fake_result = [{
        "citation": fake_text,
        "paper_exists": False,
        "citation_accurate": False,
        "hallucination_type": "Fabricated Citation",
        "metadata_errors": ["Paper not found in Crossref, Semantic Scholar or OpenAlex."],
        "matched_title": None,
        "matched_authors": [],
        "matched_year": None,
        "matched_venue": None,
        "matched_doi": None,
    }]

    with patch("app.services.correction_service.verify_response", return_value=fake_result), \
         patch("app.services.correction_service.search_replacement_paper", return_value=None):
        res = correct_and_reverify_response(fake_text, max_iterations=2)

        assert res["verification_summary"]["final_status"] != "verified"
        assert res["verification_summary"]["unresolved_count"] == 1
        # Confirms warning was attached and no replacement paper was hallucinated
        assert ("UNVERIFIED REFERENCE" in res["final_response"] or "[Warning: Claim-to-source mismatch" in res["final_response"])


# ==============================================================================
# SCENARIO 8: A correction introduces a new citation that must be checked.
# ==============================================================================
def test_08_correction_introduces_new_citation_checked_in_iteration_2():
    flawed_text = """1. Transformer Intro
Authors: Unknown
Year: 2017"""

    call_count = 0

    def mock_verify(text, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return [{
                "citation": flawed_text,
                "paper_exists": True,
                "citation_accurate": False,
                "metadata_errors": ["Author mismatch", "Title mismatch"],
                "matched_title": "Attention Is All You Need",
                "matched_authors": ["Ashish Vaswani et al."],
                "matched_year": 2017,
                "matched_venue": "NeurIPS",
                "matched_doi": "10.48550/arXiv.1706.03762",
                "matched_abstract": "Attention mechanism.",
                "hallucination_type": "Metadata Hallucination",
            }]
        else:
            # Check that the text passed to verify_response in iteration 2 contains the new citation
            assert "Attention Is All You Need" in text
            return [{
                "citation": text.strip(),
                "paper_exists": True,
                "citation_accurate": True,
                "metadata_errors": [],
                "matched_title": "Attention Is All You Need",
                "matched_authors": ["Ashish Vaswani et al."],
                "matched_year": 2017,
                "matched_venue": "NeurIPS",
                "matched_doi": "10.48550/arXiv.1706.03762",
                "matched_abstract": "Attention mechanism.",
                "hallucination_type": "Valid Citation",
            }]

    with patch("app.services.correction_service.verify_response", side_effect=mock_verify):
        res = correct_and_reverify_response(flawed_text, max_iterations=2)
        assert call_count == 2
        assert res["verification_summary"]["final_status"] == "verified"


# ==============================================================================
# SCENARIO 9: External APIs fail or return rate-limit errors.
# ==============================================================================
def test_09_external_apis_fail_marked_unverified_outage():
    text = """1. ResNet Paper
Authors: Kaiming He et al.
Year: 2016"""

    outage_result = [{
        "citation": text,
        "paper_exists": None,
        "citation_accurate": False,
        "hallucination_type": "Unverified / Provider Outage",
        "metadata_errors": ["All scholarly metadata providers were unreachable."],
        "matched_title": None,
        "matched_authors": [],
        "matched_year": None,
        "matched_venue": None,
        "matched_doi": None,
        "matched_abstract": None,
    }]

    with patch("app.services.correction_service.verify_response", return_value=outage_result):
        res = correct_and_reverify_response(text, max_iterations=2)

        assert res["verification_summary"]["final_status"] == "unverified"
        assert res["verification_summary"]["final_status"] != "verified"
        assert "unreachable" in res["verification_summary"]["limitations"].lower()


# ==============================================================================
# SCENARIO 10: Correction attempts are exhausted and discrepancies remain.
# ==============================================================================
def test_10_correction_attempts_exhausted_discrepancies_remain():
    text = """1. Mismatched Complex Paper
Authors: Wrong Authors
Year: 1900"""

    persistent_error = [{
        "citation": text,
        "paper_exists": True,
        "citation_accurate": False,
        "hallucination_type": "Metadata Hallucination",
        "metadata_errors": ["Persistent Author mismatch"],
        "matched_title": None,
        "matched_authors": [],
        "matched_year": None,
        "matched_venue": None,
        "matched_doi": None,
        "matched_abstract": None,
    }]

    with patch("app.services.correction_service.verify_response", return_value=persistent_error):
        res = correct_and_reverify_response(text, max_iterations=2)

        assert res["verification_summary"]["final_status"] in ["correction_failed", "unverified"]
        assert res["verification_summary"]["final_status"] != "verified"


# ==============================================================================
# SCENARIO 11: The response contains no citations.
# ==============================================================================
def test_11_response_contains_no_citations():
    text = "Machine learning models rely on statistical optimization and gradient descent algorithms."

    with patch("app.services.correction_service.verify_response", return_value=[]):
        res = correct_and_reverify_response(text, max_iterations=2)

        assert res["verification_summary"]["total_citations"] == 0
        assert res["verification_summary"]["unresolved_count"] == 0
        assert res["verification_summary"]["final_status"] == "verified"
        assert "No citations detected" in res["verification_summary"]["limitations"]


# ==============================================================================
# SCENARIO 12: Final response contains a mixture of verified and unresolved citations.
# ==============================================================================
def test_12_mixture_of_verified_and_unresolved_citations_is_partially_verified():
    text = """1. Deep Residual Learning for Image Recognition
Authors: Kaiming He et al.
Year: 2016
DOI: 10.1109/CVPR.2016.90

2. Fabricated Paper on Imaginary AI
Authors: Fake Author
Year: 2025"""

    mixed_result = [
        {
            "citation": "1. Deep Residual Learning for Image Recognition...",
            "paper_exists": True,
            "citation_accurate": True,
            "hallucination_type": "Valid Citation",
            "metadata_errors": [],
            "matched_title": "Deep Residual Learning for Image Recognition",
            "matched_authors": ["Kaiming He et al."],
            "matched_year": 2016,
            "matched_venue": "CVPR",
            "matched_doi": "10.1109/CVPR.2016.90",
            "matched_abstract": "Deep residual learning.",
        },
        {
            "citation": "2. Fabricated Paper on Imaginary AI...",
            "paper_exists": False,
            "citation_accurate": False,
            "hallucination_type": "Fabricated Citation",
            "metadata_errors": ["Paper not found."],
            "matched_title": None,
            "matched_authors": [],
            "matched_year": None,
            "matched_venue": None,
            "matched_doi": None,
            "matched_abstract": None,
        }
    ]

    with patch("app.services.correction_service.verify_response", return_value=mixed_result), \
         patch("app.services.correction_service.search_replacement_paper", return_value=None):
        res = correct_and_reverify_response(text, max_iterations=2)

        # Strictly must NEVER be "verified" when any citation is unresolved
        assert res["verification_summary"]["final_status"] == "partially_verified"
        assert res["verification_summary"]["final_status"] != "verified"
        assert res["verification_summary"]["verified_count"] == 1
        assert res["verification_summary"]["unresolved_count"] == 1


# ==============================================================================
# SCENARIO 13: A correction attempt introduces another invalid citation.
# ==============================================================================
def test_13_correction_introducing_another_invalid_citation_fails_truthfully():
    """
    If iteration 1 replaces a flawed citation, but the replacement still fails
    verification in iteration 2 (e.g. wrong year or new author mismatch):
    - Iteration 2 re-verifies and catches the discrepancy
    - Discrepancy is preserved
    - Retry limit prevents infinite loop
    - Final status is correction_failed, NEVER verified
    """
    flawed_text = """1. Preliminary Model Paper
Authors: Wrong Authors
Year: 2020"""

    # Iteration 1 result: Paper exists but has errors, suggesting a correction
    iter1_result = [{
        "citation": flawed_text,
        "paper_exists": True,
        "citation_accurate": False,
        "hallucination_type": "Metadata Hallucination",
        "metadata_errors": ["Author mismatch"],
        "matched_title": "Preliminary Model Paper",
        "matched_authors": ["New Authors"],
        "matched_year": 2021,
        "matched_venue": "ICML",
        "matched_doi": "10.1145/12345",
    }]

    # Iteration 2 result: The new citation in the revised text still fails verification
    iter2_result = [{
        "citation": "1. Preliminary Model Paper\nAuthors: New Authors\nYear: 2021\nVenue: ICML\nDOI: 10.1145/12345",
        "paper_exists": True,
        "citation_accurate": False,
        "hallucination_type": "Metadata Hallucination",
        "metadata_errors": ["DOI mismatch - points to unrelated workshop paper"],
        "matched_title": "Preliminary Model Paper",
        "matched_authors": ["New Authors"],
        "matched_year": 2021,
        "matched_venue": "ICML",
        "matched_doi": None,
    }]

    with patch("app.services.correction_service.verify_response", side_effect=[iter1_result, iter2_result]):
        res = correct_and_reverify_response(flawed_text, max_iterations=2)

        # Must be correction_failed, never verified
        assert res["verification_summary"]["final_status"] == "correction_failed"
        assert res["verification_summary"]["final_status"] != "verified"
        assert res["verification_summary"]["unresolved_count"] == 1
        assert res["applied_corrections"][0]["verified_in_next_step"] is False


# ==============================================================================
# SCENARIO 14: Ensuring the final response matches the re-verified corrected response.
# ==============================================================================
def test_14_ensure_final_response_matches_reverified_response():
    """
    Confirms that:
    - final_response is the exact text passed to and returned from re-verification
    - original_response remains unchanged
    - final_citation_analysis matches the citations in final_response
    """
    initial_text = """Here is the citation:

1. Attention Is All You Need
Authors: Hinton, LeCun
Year: 2019

End of response."""

    flawed_citation = """1. Attention Is All You Need
Authors: Hinton, LeCun
Year: 2019"""

    corrected_citation = """1. Attention Is All You Need
Authors: Ashish Vaswani, Noam Shazeer
Year: 2017
Venue: NeurIPS
DOI: 10.48550/arXiv.1706.03762"""

    iter1_result = [{
        "citation": flawed_citation,
        "paper_exists": True,
        "citation_accurate": False,
        "hallucination_type": "Metadata Hallucination",
        "metadata_errors": ["Author mismatch"],
        "matched_title": "Attention Is All You Need",
        "matched_authors": ["Ashish Vaswani", "Noam Shazeer"],
        "matched_year": 2017,
        "matched_venue": "NeurIPS",
        "matched_doi": "10.48550/arXiv.1706.03762",
    }]

    iter2_result = [{
        "citation": corrected_citation,
        "paper_exists": True,
        "citation_accurate": True,
        "hallucination_type": "Valid Citation",
        "metadata_errors": [],
        "matched_title": "Attention Is All You Need",
        "matched_authors": ["Ashish Vaswani", "Noam Shazeer"],
        "matched_year": 2017,
        "matched_venue": "NeurIPS",
        "matched_doi": "10.48550/arXiv.1706.03762",
    }]

    with patch("app.services.correction_service.verify_response", side_effect=[iter1_result, iter2_result]):
        res = correct_and_reverify_response(initial_text, max_iterations=2)

        # 1. final_response has the corrected text, not the original flawed text
        assert "Ashish Vaswani" in res["final_response"]
        assert "Hinton, LeCun" not in res["final_response"]

        # 2. original_response retains the original flawed text
        assert "Hinton, LeCun" in res["original_response"]
        assert "Ashish Vaswani" not in res["original_response"]

        # 3. Final citations correspond to final_response
        assert len(res["final_citation_analysis"]) == 1
        assert res["final_citation_analysis"][0]["citation_accurate"] is True
        assert res["verification_summary"]["final_status"] == "verified"


# ==============================================================================
# SCENARIO 15: Robust replacement with CRLF line endings and trailing spaces.
# ==============================================================================
def test_15_robust_replacement_with_crlf_and_whitespace():
    from app.services.correction_service import replace_citation_in_text

    # CRLF with trailing spaces
    original = "1. Title Here  \r\nAuthors: Old Author \r\nYear: 2020\r\n"
    old_cit = "1. Title Here\nAuthors: Old Author\nYear: 2020"
    new_cit = "1. Title Here\nAuthors: Verified Author\nYear: 2020"

    result = replace_citation_in_text(original, old_cit, new_cit)
    assert "Verified Author" in result
    assert "Old Author" not in result


# ==============================================================================
# SCENARIO 16: Corrupted Transformer citation rectified, re-verified, canonical citation present
# ==============================================================================
def test_16_corrupted_transformer_citation_reverified_with_canonical_citation_and_field_integrity():
    """
    Simulates the exact scenario from the screenshot:
    - Initial submitted citation has corrupted authors (Hinton, LeCun, Bengio),
      corrupted venue (Nature Machine Intelligence), corrupted year (2019),
      and corrupted DOI (10.1038/s42256-019-0001-x).
    - Closed-loop rectifies citation using canonical metadata:
      Vaswani et al., 2017, NeurIPS, DOI 10.48550/arXiv.1706.03762.
    - Iteration 2 re-verifies the corrected citation independently.
    - Asserts that:
      * Overall status is strictly 'verified' (unresolved_count == 0)
      * Re-verified citation has citation_accurate is True, metadata_errors == []
      * Re-verified citation has year_match is True, venue_match is True, doi_match is True
      * canonical_citation is populated with genuine IEEE format and not None
      * Initial citation retains all original errors in initial_citation_analysis for audit provenance
    """
    initial_text = """Here is the reference for the Transformer paper:

1. Attention Is All You Need
Authors: Geoffrey Hinton, Yann LeCun, Yoshua Bengio
Year: 2019
Venue: Nature Machine Intelligence
DOI: 10.1038/s42256-019-0001-x"""

    initial_flawed_result = [{
        "citation": """1. Attention Is All You Need
Authors: Geoffrey Hinton, Yann LeCun, Yoshua Bengio
Year: 2019
Venue: Nature Machine Intelligence
DOI: 10.1038/s42256-019-0001-x""",
        "paper_exists": True,
        "citation_accurate": False,
        "hallucination_type": "Metadata Hallucination",
        "metadata_errors": [
            "Author mismatch",
            "Publication year mismatch",
            "Venue mismatch",
            "DOI mismatch",
        ],
        "matched_title": "Attention Is All You Need",
        "matched_authors": ["Ashish Vaswani", "Noam Shazeer", "Niki Parmar", "Jakob Uszkoreit"],
        "matched_year": 2017,
        "matched_venue": "Advances in Neural Information Processing Systems (NeurIPS)",
        "matched_doi": "10.48550/arXiv.1706.03762",
        "matched_abstract": "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks.",
        "candidate_score": 85.0,
        "title_similarity": 100.0,
        "author_similarity": 15.0,
        "year_match": False,
        "venue_match": False,
        "doi_match": False,
        "hallucination_score": 75,
        "confidence": "Paper Exists but Citation Contains Errors",
        "corrected_citation": "A. Vaswani, N. Shazeer, N. Parmar, J. Uszkoreit, \"Attention Is All You Need,\" Advances in Neural Information Processing Systems (NeurIPS), 2017. DOI: 10.48550/arXiv.1706.03762",
        "canonical_citation": "A. Vaswani, N. Shazeer, N. Parmar, J. Uszkoreit, \"Attention Is All You Need,\" Advances in Neural Information Processing Systems (NeurIPS), 2017. DOI: 10.48550/arXiv.1706.03762",
        "reason": [
            "Paper found in scholarly databases.",
            "Paper title matches.",
            "Authors differ.",
            "Publication year differs.",
            "Venue differs.",
            "DOI differs.",
        ],
        "parsed": {
            "title": "Attention Is All You Need",
            "authors": ["Geoffrey Hinton", "Yann LeCun", "Yoshua Bengio"],
            "year": 2019,
            "venue": "Nature Machine Intelligence",
            "doi": "10.1038/s42256-019-0001-x",
        },
    }]

    reverified_clean_result = [{
        "citation": """1. Attention Is All You Need
Authors: Ashish Vaswani, Noam Shazeer, Niki Parmar, Jakob Uszkoreit
Year: 2017
Venue: Advances in Neural Information Processing Systems (NeurIPS)
DOI: 10.48550/arXiv.1706.03762""",
        "paper_exists": True,
        "citation_accurate": True,
        "hallucination_type": "Valid Citation",
        "metadata_errors": [],
        "matched_title": "Attention Is All You Need",
        "matched_authors": ["Ashish Vaswani", "Noam Shazeer", "Niki Parmar", "Jakob Uszkoreit"],
        "matched_year": 2017,
        "matched_venue": "Advances in Neural Information Processing Systems (NeurIPS)",
        "matched_doi": "10.48550/arXiv.1706.03762",
        "matched_abstract": "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks.",
        "candidate_score": 100.0,
        "title_similarity": 100.0,
        "author_similarity": 100.0,
        "year_match": True,
        "venue_match": True,
        "doi_match": True,
        "hallucination_score": 0,
        "confidence": "Verified Citation",
        "corrected_citation": None,
        "canonical_citation": "A. Vaswani, N. Shazeer, N. Parmar, J. Uszkoreit, \"Attention Is All You Need,\" Advances in Neural Information Processing Systems (NeurIPS), 2017. DOI: 10.48550/arXiv.1706.03762",
        "reason": [
            "Paper found in scholarly databases.",
            "Paper title matches.",
            "Authors match.",
            "Publication year matches.",
            "Venue matches.",
            "DOI verified.",
        ],
        "parsed": {
            "title": "Attention Is All You Need",
            "authors": ["Ashish Vaswani", "Noam Shazeer", "Niki Parmar", "Jakob Uszkoreit"],
            "year": 2017,
            "venue": "Advances in Neural Information Processing Systems (NeurIPS)",
            "doi": "10.48550/arXiv.1706.03762",
        },
    }]

    with patch("app.services.correction_service.verify_response", side_effect=[initial_flawed_result, reverified_clean_result]):
        res = correct_and_reverify_response(initial_text, max_iterations=2)

        # 1. Overall status must agree with zero unresolved discrepancies
        assert res["verification_summary"]["final_status"] == "verified"
        assert res["verification_summary"]["unresolved_count"] == 0
        assert res["verification_summary"]["verified_count"] == 1
        assert res["verification_summary"]["corrected_and_verified_count"] == 1

        # 2. Final citation analysis is genuinely the corrected version
        final_cit = res["final_citation_analysis"][0]
        assert final_cit["citation_accurate"] is True
        assert final_cit["metadata_errors"] == []
        assert final_cit["doi_match"] is True
        assert final_cit["year_match"] is True
        assert final_cit["venue_match"] is True
        assert final_cit["author_similarity"] >= 70
        assert final_cit["canonical_citation"] is not None
        assert "10.48550/arXiv.1706.03762" in final_cit["canonical_citation"]

        # 3. Initial citation analysis preserves the submitted discrepancies for audit
        init_cit = res["initial_citation_analysis"][0]
        assert init_cit["citation_accurate"] is False
        assert len(init_cit["metadata_errors"]) == 4
        assert "Author mismatch" in init_cit["metadata_errors"]
        assert "DOI mismatch" in init_cit["metadata_errors"]


# ==============================================================================
# SCENARIO 17: Correction that still contains an invalid DOI remains unverified
# ==============================================================================
def test_17_correction_with_unresolved_invalid_doi_remains_unverified():
    """
    Verifies that if a correction introduces or retains an invalid DOI:
    - Iteration 2 detects the DOI mismatch
    - The response is NOT marked as verified
    - final_status is 'correction_failed'
    - unresolved_count >= 1
    - applied_corrections verified_in_next_step is False
    """
    initial_text = """1. Graph Neural Networks
Authors: Alice Smith
Year: 2021
DOI: 10.1109/wrong.doi.2021"""

    iter1_result = [{
        "citation": """1. Graph Neural Networks
Authors: Alice Smith
Year: 2021
DOI: 10.1109/wrong.doi.2021""",
        "paper_exists": True,
        "citation_accurate": False,
        "hallucination_type": "Metadata Hallucination",
        "metadata_errors": ["DOI mismatch"],
        "matched_title": "Graph Neural Networks",
        "matched_authors": ["Alice Smith"],
        "matched_year": 2021,
        "matched_venue": "IEEE Trans",
        "matched_doi": "10.1109/GNN.2021.12345",
    }]

    # In iteration 2, the citation still has an invalid/corrupted DOI
    iter2_result = [{
        "citation": """1. Graph Neural Networks
Authors: Alice Smith
Year: 2021
Venue: IEEE Trans
DOI: 10.9999/still.invalid.doi""",
        "paper_exists": True,
        "citation_accurate": False,
        "hallucination_type": "Metadata Hallucination",
        "metadata_errors": ["DOI mismatch"],
        "matched_title": "Graph Neural Networks",
        "matched_authors": ["Alice Smith"],
        "matched_year": 2021,
        "matched_venue": "IEEE Trans",
        "matched_doi": "10.1109/GNN.2021.12345",
        "doi_match": False,
    }]

    with patch("app.services.correction_service.verify_response", side_effect=[iter1_result, iter2_result]):
        res = correct_and_reverify_response(initial_text, max_iterations=2)

        # Must NOT be marked fully verified
        assert res["verification_summary"]["final_status"] != "verified"
        assert res["verification_summary"]["final_status"] == "correction_failed"
        assert res["verification_summary"]["unresolved_count"] == 1
        assert res["applied_corrections"][0]["verified_in_next_step"] is False

        # Final citation analysis explicitly shows the unresolved DOI error
        final_cit = res["final_citation_analysis"][0]
        assert final_cit["citation_accurate"] is False
        assert "DOI mismatch" in final_cit["metadata_errors"]
        assert final_cit["doi_match"] is False




# ==============================================================================
# SCENARIO 18: Free-text IEEE citation with corrupted authors and venue
# ==============================================================================
def test_18_corrupted_ieee_free_text_author_and_venue_detected_and_corrected():
    """
    Verifies that a free-text IEEE citation with corrupted authors and venue:
    - Parses authors and venue correctly from the text
    - Identifies author mismatch and venue mismatch in iteration 1
    - Corrects to canonical metadata in iteration 2
    - Re-verifies to verified status with 0 unresolved discrepancies
    """
    corrupted_ieee = "John Doe and Jane Smith, 'Attention is All You Need', in Harvard Business Review, 2017. doi: 10.5555/3295222.3295349"
    cand = [{
        "title": "Attention is All You Need",
        "authors": ["Ashish Vaswani", "Noam Shazeer", "Niki Parmar", "Jakob Uszkoreit"],
        "year": 2017,
        "venue": "Advances in Neural Information Processing Systems",
        "doi": "10.5555/3295222.3295349",
        "source": "Crossref",
    }]

    with patch("app.services.verification_pipeline.retrieve_candidates", return_value=cand), \
         patch("app.services.crossref_service.verify_doi", return_value=cand[0]):
        res = correct_and_reverify_response(corrupted_ieee, max_iterations=2)

        # Iteration 1 must detect discrepancies
        assert res["audit_trail"][0]["discrepancy_count"] >= 1
        iter1_errors = res["audit_trail"][0]["discrepancies_detected"][0]["errors"]
        assert "Author mismatch" in iter1_errors
        assert "Venue mismatch" in iter1_errors

        # Correction was applied and verified
        assert len(res["applied_corrections"]) == 1
        assert res["applied_corrections"][0]["verified_in_next_step"] is True
        assert res["verification_summary"]["final_status"] == "verified"
        assert res["verification_summary"]["unresolved_count"] == 0


# ==============================================================================
# SCENARIO 19: Nonexistent DOI cannot be verified as accurate
# ==============================================================================
def test_19_nonexistent_doi_cannot_be_verified_as_accurate():
    """
    A citation providing a fake/nonexistent DOI that fails resolution must NOT
    be marked citation_accurate = True, even if the paper exists in registry.
    """
    citation = """Title: "Attention is All You Need"
Authors: Ashish Vaswani, Noam Shazeer
Year: 2017
Venue: Advances in Neural Information Processing Systems
DOI: 10.9999/fake.nonexistent.doi"""

    cand = [{
        "title": "Attention is All You Need",
        "authors": ["Ashish Vaswani", "Noam Shazeer"],
        "year": 2017,
        "venue": "Advances in Neural Information Processing Systems",
        "doi": "10.5555/3295222.3295349",
        "source": "Crossref",
    }]

    # verify_doi returns None (404 / failed resolution for 10.9999/fake)
    with patch("app.services.verification_pipeline.retrieve_candidates", return_value=cand), \
         patch("app.services.crossref_service.verify_doi", return_value=None):
        results = verify_response(citation)
        assert len(results) == 1
        r = results[0]
        assert r["paper_exists"] is True
        assert r["citation_accurate"] is False
        assert "DOI mismatch" in r["metadata_errors"]
        assert r["doi_match"] is False


# ==============================================================================
# SCENARIO 20: Resolving DOI pointing to unrelated paper rejected
# ==============================================================================
def test_20_resolving_doi_pointing_to_unrelated_paper_rejected():
    """
    If a citation supplies a valid DOI that resolves, but to an unrelated publication,
    the pipeline must reject it with DOI mismatch.
    """
    citation = """Title: "Deep Residual Learning for Image Recognition"
Authors: Kaiming He, Xiangyu Zhang, Shaoqing Ren, Jian Sun
Year: 2016
Venue: CVPR
DOI: 10.1145/1146238.1146241"""

    cand_resnet = [{
        "title": "Deep Residual Learning for Image Recognition",
        "authors": ["Kaiming He", "Xiangyu Zhang", "Shaoqing Ren", "Jian Sun"],
        "year": 2016,
        "venue": "CVPR",
        "doi": "10.1109/CVPR.2016.90",
        "source": "Crossref",
    }]

    unrelated_doi_paper = {
        "title": "The species per path approach to SearchBased test data generation",
        "authors": ["Phil McMinn", "Mark Harman", "David Binkley", "Paolo Tonella"],
        "year": 2006,
        "venue": "ISSTA",
        "doi": "10.1145/1146238.1146241",
        "source": "Crossref",
    }

    with patch("app.services.verification_pipeline.retrieve_candidates", return_value=cand_resnet), \
         patch("app.services.crossref_service.verify_doi", return_value=unrelated_doi_paper):
        results = verify_response(citation)
        assert len(results) == 1
        r = results[0]
        assert r["paper_exists"] is True
        assert r["citation_accurate"] is False
        assert "DOI mismatch" in r["metadata_errors"]


# ==============================================================================
# SCENARIO 21: Incomplete citation missing authors or year fails accuracy
# ==============================================================================
def test_21_incomplete_citation_without_authors_or_year_fails_accuracy():
    """
    A citation containing only a title without authors or year (and no resolving DOI)
    lacks essential bibliographic completeness and cannot be certified as accurate.
    """
    citation = '[1] "Deep Residual Learning for Image Recognition"'
    cand = [{
        "title": "Deep Residual Learning for Image Recognition",
        "authors": ["Kaiming He", "Xiangyu Zhang"],
        "year": 2016,
        "venue": "CVPR",
        "doi": "10.1109/CVPR.2016.90",
        "source": "Crossref",
    }]

    with patch("app.services.verification_pipeline.retrieve_candidates", return_value=cand), \
         patch("app.services.crossref_service.verify_doi", return_value=None):
        results = verify_response(citation)
        assert len(results) == 1
        r = results[0]
        assert r["paper_exists"] is True
        assert r["citation_accurate"] is False
        assert "Author metadata missing" in r["metadata_errors"]
        assert "Publication year missing" in r["metadata_errors"]


# ==============================================================================
# SCENARIO 22: Short surname false-positive prevention
# ==============================================================================
def test_22_short_surname_collision_prevention():
    """
    Verifies that 2-letter or short surnames are never falsely matched via substring
    containment (e.g. He vs Chen, Li vs Williams, An vs Zhang).
    """
    from app.services.similarity_service import authors_match_single, compare_authors

    assert authors_match_single("Kaiming He", "K. Chen") is False
    assert authors_match_single("J. Li", "J. Williams") is False
    assert authors_match_single("Xiaoming An", "X. Zhang") is False
    assert authors_match_single("Wei Wu", "W. Kruwulski") is False

    # True matches should succeed
    assert authors_match_single("Kaiming He", "K. He") is True
    assert authors_match_single("Ashish Vaswani", "A. Vaswani") is True
    assert authors_match_single("A. Smith-Jones", "A. Jones") is True

    # Multi-author list comparison
    score = compare_authors(["Kaiming He"], ["K. Chen"])
    assert score < 70.0


# ==============================================================================
# SCENARIO 23: Wrong-paper candidate selection rejected; never substituted
# ==============================================================================
def test_23_wrong_paper_candidate_rejected_never_substituted():
    """
    Verifies that a candidate with a similar title but completely different authors
    is rejected as non-viable, and the system never substitutes the wrong paper
    into the response as a 'correction'.
    """
    citation = '''1. Generative Adversarial Networks
Authors: Ian Goodfellow, Jean Pouget-Abadie, Mehdi Mirza
Year: 2014
Venue: NIPS'''

    # Candidate with similar title but completely different authors
    wrong_paper_candidate = [{
        "title": "Generative Adversarial Networks: An Overview",
        "authors": ["Antonia Creswell", "Tom White", "Vincent Dumoulin"],
        "year": 2018,
        "venue": "IEEE Signal Processing Magazine",
        "doi": "10.1109/MSP.2017.2765202",
        "source": "Crossref",
    }]

    with patch("app.services.verification_pipeline.retrieve_candidates", return_value=wrong_paper_candidate), \
         patch("app.services.crossref_service.verify_doi", return_value=None):
        res = correct_and_reverify_response(citation, max_iterations=2)

        # Must NOT be marked verified
        assert res["verification_summary"]["final_status"] != "verified"
        assert res["verification_summary"]["unresolved_count"] >= 1

        # Must not substitute the wrong paper
        final_text = res["final_response"]
        assert "Antonia Creswell" not in final_text
        assert "IEEE Signal Processing Magazine" not in final_text


# ==============================================================================
# SCENARIO 24: Unrelated resolving DOI fails verification and is never marked verified
# ==============================================================================
def test_24_unrelated_resolving_doi_fails_verification_and_never_verified():
    """
    If a citation supplies a DOI that resolves, but belongs to an entirely unrelated
    publication, the pipeline must:
    - Mark DOI status as mismatch (never verified)
    - Identify DOI mismatch in metadata errors
    - Retain DOI mismatch in reason trail
    """
    citation = '''Title: "Graph Attention Networks"
Authors: Petar Velickovic, Guillem Cucurull, Arantxa Casanova, Adriana Romero, Pietro Lio, Yoshua Bengio
Year: 2018
Venue: ICLR
DOI: 10.1145/1146238.1146241'''

    real_gat = [{
        "title": "Graph Attention Networks",
        "authors": ["Petar Velickovic", "Guillem Cucurull", "Arantxa Casanova", "Adriana Romero", "Pietro Lio", "Yoshua Bengio"],
        "year": 2018,
        "venue": "ICLR",
        "doi": "10.48550/arxiv.1710.10903",
        "source": "Crossref",
    }]

    unrelated_doi_paper = {
        "title": "The species per path approach to SearchBased test data generation",
        "authors": ["Phil McMinn", "Mark Harman", "David Binkley", "Paolo Tonella"],
        "year": 2006,
        "venue": "ISSTA",
        "doi": "10.1145/1146238.1146241",
        "source": "Crossref",
    }

    with patch("app.services.verification_pipeline.retrieve_candidates", return_value=real_gat), \
         patch("app.services.crossref_service.verify_doi", return_value=unrelated_doi_paper):
        results = verify_response(citation)
        assert len(results) == 1
        r = results[0]

        # Paper exists (via GAT record)
        assert r["paper_exists"] is True
        # Citation is inaccurate due to wrong DOI
        assert r["citation_accurate"] is False
        assert "DOI mismatch" in r["metadata_errors"]
        assert r["doi_match"] is False
        assert any("does not belong" in reas.lower() or "differs" in reas.lower() for reas in r["reason"])


# ==============================================================================
# SCENARIO 25: Erroneous year prefers primary original publication over reprints
# ==============================================================================
def test_25_wrong_year_prefers_primary_original_publication():
    """
    When a citation provides an incorrect year, candidate ranking and canonicalization
    must select the primary original publication (e.g. 2017 NeurIPS), not a later reprint (e.g. 2021 CACM).
    """
    citation = '''1. Attention is All You Need
Authors: Ashish Vaswani, Noam Shazeer
Year: 2024
Venue: Advances in Neural Information Processing Systems'''

    cand_primary = {
        "title": "Attention is All You Need",
        "authors": ["Ashish Vaswani", "Noam Shazeer"],
        "year": 2017,
        "venue": "Advances in Neural Information Processing Systems",
        "doi": "10.5555/3295222.3295349",
        "source": "Crossref",
    }

    cand_reprint = {
        "title": "Attention is all you need",
        "authors": ["Ashish Vaswani", "Noam Shazeer"],
        "year": 2021,
        "venue": "Communications of the ACM",
        "doi": "10.1145/3447772",
        "source": "Crossref",
    }

    with patch("app.services.verification_pipeline.retrieve_candidates", return_value=[cand_reprint, cand_primary]), \
         patch("app.services.crossref_service.verify_doi", return_value=cand_primary):
        res = correct_and_reverify_response(citation, max_iterations=2)

        # Iteration 1 detects year mismatch
        assert res["audit_trail"][0]["discrepancy_count"] >= 1
        assert "Publication year mismatch" in res["audit_trail"][0]["discrepancies_detected"][0]["errors"]

        # Final response is corrected to the original 2017 conference version
        assert "2017" in res["final_response"]
        assert "Advances in Neural Information Processing Systems" in res["final_response"]
        assert res["verification_summary"]["final_status"] == "verified"
        assert res["verification_summary"]["unresolved_count"] == 0


# ==============================================================================
# SCENARIO 26: Wrong venue detected and corrected to canonical venue
# ==============================================================================
def test_26_wrong_venue_detected_and_corrected_to_canonical_venue():
    """
    A citation providing an incorrect venue (e.g. Nature Machine Intelligence instead of ICML)
    is flagged for venue mismatch and corrected to the canonical registry venue.
    """
    citation = '''Title: "Mastering the Game of Go with Deep Neural Networks and Tree Search"
Authors: David Silver, Aja Huang, Chris J. Maddison
Year: 2016
Venue: ICML'''

    cand_nature = [{
        "title": "Mastering the Game of Go with Deep Neural Networks and Tree Search",
        "authors": ["David Silver", "Aja Huang", "Chris J. Maddison"],
        "year": 2016,
        "venue": "Nature",
        "doi": "10.1038/nature16961",
        "source": "Crossref",
    }]

    with patch("app.services.verification_pipeline.retrieve_candidates", return_value=cand_nature), \
         patch("app.services.crossref_service.verify_doi", return_value=cand_nature[0]):
        res = correct_and_reverify_response(citation, max_iterations=2)

        # Iteration 1 detects venue mismatch
        assert "Venue mismatch" in res["audit_trail"][0]["discrepancies_detected"][0]["errors"]

        # Final response is corrected to Nature
        assert "Nature" in res["final_response"]
        assert res["verification_summary"]["final_status"] == "verified"
        assert res["verification_summary"]["unresolved_count"] == 0


# ==============================================================================
# SCENARIO 27: Chimera citation with unresolvable intended paper remains unverified
# ==============================================================================
def test_27_chimera_citation_with_unresolvable_intended_paper_preserves_unresolved_status():
    """
    A chimera citation combines an unindexed/fabricated title with a real resolving DOI
    belonging to an unrelated paper. Multi-source retrieval yields 0 candidates for the title.
    The system must NOT adopt the unrelated DOI paper as the intended candidate.
    It must preserve the unresolved status, transparently qualify the citation, and
    never present the replacement as verified.
    """
    citation = '''Title: "Completely Fabricated Quantum Neural Network Model for Teleportation"
Authors: Fake Author One, Fake Author Two
Year: 2022
DOI: 10.1145/1146238.1146241'''

    unrelated_doi_paper = {
        "title": "The species per path approach to SearchBased test data generation",
        "authors": ["Phil McMinn", "Mark Harman", "David Binkley", "Paolo Tonella"],
        "year": 2006,
        "venue": "ISSTA",
        "doi": "10.1145/1146238.1146241",
        "source": "Crossref",
    }

    with patch("app.services.verification_pipeline.retrieve_candidates", return_value=[]), \
         patch("app.services.crossref_service.verify_doi", return_value=unrelated_doi_paper):
        res = correct_and_reverify_response(citation, max_iterations=2)

        # Must not adopt McMinn et al. as verified replacement
        assert res["verification_summary"]["final_status"] in ["unverified", "correction_failed"]
        assert res["verification_summary"]["unresolved_count"] >= 1
        assert "The species per path approach" not in res["final_response"]
        assert ("UNVERIFIED REFERENCE" in res["final_response"] or "[Warning: Claim-to-source mismatch" in res["final_response"])


# ==============================================================================
# SCENARIO A: Exact Mismatched-DOI Diagnostic Case (Section 1 of Specification)
# ==============================================================================
def test_scenario_a_exact_mismatched_doi_transformer_case():
    """
    A. The exact mismatched-DOI case described in prompt Section 1:
    Citation:
    Title: Attention Is All You Need
    Authors: Ashish Vaswani, Noam Shazeer, Niki Parmar, Jakob Uszkoreit, Llion Jones, Aidan N. Gomez, Lukasz Kaiser, Illia Polosukhin
    Year: 2017
    Venue: Advances in Neural Information Processing Systems
    DOI: 10.1038/s41586-020-2649-2 (deliberately mismatched, resolves to NumPy)

    Expected:
    - Iteration 1 detects wrong DOI (resolves to unrelated paper).
    - Correction retrieves and selects the intended canonical record (10.48550/arxiv.1706.03762).
    - Iteration 2 re-verifies the corrected citation against canonical evidence.
    - Final status is "verified" with zero unresolved discrepancies.
    - Corrected DOI belongs to the Transformer publication.
    """
    citation = """Title: Attention Is All You Need
Authors: Ashish Vaswani, Noam Shazeer, Niki Parmar, Jakob Uszkoreit, Llion Jones, Aidan N. Gomez, Lukasz Kaiser, Illia Polosukhin
Year: 2017
Venue: Advances in Neural Information Processing Systems
DOI: 10.1038/s41586-020-2649-2"""

    unrelated_numpy_doi = {
        "title": "Array programming with NumPy",
        "authors": ["Charles R. Harris", "K. Jarrod Millman", "Stéfan J. van der Walt"],
        "year": 2020,
        "venue": "Nature",
        "doi": "10.1038/s41586-020-2649-2",
        "source": "Crossref",
    }

    canonical_transformer_cand = {
        "title": "Attention Is All You Need",
        "authors": [
            "Ashish Vaswani", "Noam Shazeer", "Niki Parmar", "Jakob Uszkoreit",
            "Llion Jones", "Aidan N. Gomez", "Lukasz Kaiser", "Illia Polosukhin"
        ],
        "year": 2017,
        "alternate_years": [2017],
        "venue": "Advances in Neural Information Processing Systems",
        "doi": "10.48550/arxiv.1706.03762",
        "source": "DataCite",
        "provenance": {
            "primary_source": "DataCite",
            "retrieved_title": "Attention Is All You Need",
            "retrieved_authors": ["Ashish Vaswani", "Noam Shazeer", "Niki Parmar", "Jakob Uszkoreit", "Llion Jones", "Aidan N. Gomez", "Lukasz Kaiser", "Illia Polosukhin"],
            "retrieved_year": 2017,
            "retrieved_venue": "Advances in Neural Information Processing Systems",
            "retrieved_doi": "10.48550/arxiv.1706.03762",
            "sources_corroborating": ["DataCite", "OpenAlex"],
        }
    }

    def mock_verify_doi(doi):
        clean_d = str(doi).strip().lower()
        if "10.1038/s41586-020-2649-2" in clean_d:
            return unrelated_numpy_doi
        if "10.48550/arxiv.1706.03762" in clean_d:
            return canonical_transformer_cand
        return None

    def mock_retrieve_candidates(title, authors=None, year=None, doi=None):
        if "attention" in str(title).lower():
            return [canonical_transformer_cand]
        return []

    with patch("app.services.verification_pipeline.retrieve_candidates", side_effect=mock_retrieve_candidates), \
         patch("app.services.crossref_service.verify_doi", side_effect=mock_verify_doi):

        res = correct_and_reverify_response(citation, max_iterations=2)

        # Iteration 1 detected the mismatched DOI
        assert len(res["audit_trail"]) >= 1
        it1_disc = res["audit_trail"][0]["discrepancies_detected"]
        assert len(it1_disc) == 1
        assert "DOI mismatch" in it1_disc[0]["errors"]

        # Applied correction used canonical record
        assert len(res["applied_corrections"]) == 1
        corr = res["applied_corrections"][0]
        assert "10.48550/arXiv.1706.03762" in corr["corrected_citation"]
        assert "2017" in corr["corrected_citation"]
        assert corr["verified_in_next_step"] is True

        # Final verification status is fully verified with 0 unresolved
        assert res["verification_summary"]["final_status"] == "verified"
        assert res["verification_summary"]["unresolved_count"] == 0
        assert res["verification_summary"]["verified_count"] == 1
        assert res["verification_summary"]["corrected_and_verified_count"] == 1

        # Final citation analysis checks
        c0 = res["final_citation_analysis"][0]
        assert c0["paper_exists"] is True
        assert c0["citation_accurate"] is True
        assert c0["doi_match"] is True
        assert c0["year_match"] is True
        assert c0["venue_match"] is True
        assert c0["metadata_errors"] == []


# ==============================================================================
# SCENARIO B: DOI Resolves Successfully but Belongs to a Different Paper
# ==============================================================================
def test_scenario_b_doi_resolves_to_different_paper():
    """
    B. A DOI that resolves successfully but belongs to a different paper.
    Must not adopt the unrelated paper or validate the citation.
    """
    citation = """1. "Deep Residual Learning for Image Recognition"
Authors: Kaiming He, Xiangyu Zhang, Shaoqing Ren, Jian Sun
Year: 2016
Venue: CVPR
DOI: 10.1038/s41586-020-2649-2"""

    unrelated_doi_paper = {
        "title": "Array programming with NumPy",
        "authors": ["Charles R. Harris", "K. Jarrod Millman"],
        "year": 2020,
        "venue": "Nature",
        "doi": "10.1038/s41586-020-2649-2",
        "source": "Crossref",
    }

    real_resnet = [{
        "title": "Deep Residual Learning for Image Recognition",
        "authors": ["Kaiming He", "Xiangyu Zhang", "Shaoqing Ren", "Jian Sun"],
        "year": 2016,
        "venue": "CVPR",
        "doi": "10.1109/CVPR.2016.90",
        "source": "Crossref",
    }]

    with patch("app.services.verification_pipeline.retrieve_candidates", return_value=real_resnet), \
         patch("app.services.crossref_service.verify_doi", return_value=unrelated_doi_paper):

        results = verify_response(citation)
        assert len(results) == 1
        r = results[0]

        assert r["paper_exists"] is True
        assert r["citation_accurate"] is False
        assert r["doi_match"] is False
        assert "DOI mismatch" in r["metadata_errors"]
        assert any("does not belong" in reas.lower() for reas in r["reason"])


# ==============================================================================
# SCENARIO C: A Correct Citation That Should Remain Unchanged
# ==============================================================================
def test_scenario_c_correct_citation_remains_unchanged():
    """
    C. A correct citation that should remain completely unchanged.
    """
    citation = """Title: Deep Residual Learning for Image Recognition
Authors: Kaiming He, Xiangyu Zhang, Shaoqing Ren, Jian Sun
Year: 2016
Venue: CVPR
DOI: 10.1109/CVPR.2016.90"""

    resnet_paper = {
        "title": "Deep Residual Learning for Image Recognition",
        "authors": ["Kaiming He", "Xiangyu Zhang", "Shaoqing Ren", "Jian Sun"],
        "year": 2016,
        "venue": "CVPR",
        "doi": "10.1109/CVPR.2016.90",
        "source": "Crossref",
    }

    with patch("app.services.verification_pipeline.retrieve_candidates", return_value=[resnet_paper]), \
         patch("app.services.crossref_service.verify_doi", return_value=resnet_paper):

        res = correct_and_reverify_response(citation, max_iterations=2)

        assert res["verification_summary"]["final_status"] == "verified"
        assert res["verification_summary"]["unresolved_count"] == 0
        assert res["verification_summary"]["verified_count"] == 1
        assert len(res["applied_corrections"]) == 0
        assert res["final_response"] == citation


# ==============================================================================
# SCENARIO D: An Incorrect Publication Year
# ==============================================================================
def test_scenario_d_incorrect_publication_year():
    """
    D. An incorrect publication year detected and corrected to canonical original year.
    """
    citation = """Title: Attention Is All You Need
Authors: Ashish Vaswani, Noam Shazeer
Year: 2025
Venue: Advances in Neural Information Processing Systems"""

    paper_record = {
        "title": "Attention Is All You Need",
        "authors": ["Ashish Vaswani", "Noam Shazeer"],
        "year": 2017,
        "alternate_years": [2017],
        "venue": "Advances in Neural Information Processing Systems",
        "doi": "10.48550/arxiv.1706.03762",
        "source": "DataCite",
    }

    with patch("app.services.verification_pipeline.retrieve_candidates", return_value=[paper_record]), \
         patch("app.services.crossref_service.verify_doi", return_value=paper_record):

        res = correct_and_reverify_response(citation, max_iterations=2)

        assert "2017" in res["final_response"]
        assert res["verification_summary"]["final_status"] == "verified"
        assert res["verification_summary"]["unresolved_count"] == 0


# ==============================================================================
# SCENARIO E: An Incorrect Publication Venue
# ==============================================================================
def test_scenario_e_incorrect_venue():
    """
    E. An incorrect venue detected and corrected to canonical registered venue.
    """
    citation = """Title: Deep Residual Learning for Image Recognition
Authors: Kaiming He, Xiangyu Zhang, Shaoqing Ren, Jian Sun
Year: 2016
Venue: International Journal of Robotics Research
DOI: 10.1109/CVPR.2016.90"""

    paper_record = {
        "title": "Deep Residual Learning for Image Recognition",
        "authors": ["Kaiming He", "Xiangyu Zhang", "Shaoqing Ren", "Jian Sun"],
        "year": 2016,
        "venue": "IEEE Conference on Computer Vision and Pattern Recognition",
        "doi": "10.1109/CVPR.2016.90",
        "source": "Crossref",
    }

    with patch("app.services.verification_pipeline.retrieve_candidates", return_value=[paper_record]), \
         patch("app.services.crossref_service.verify_doi", return_value=paper_record):

        res = correct_and_reverify_response(citation, max_iterations=2)

        assert "Computer Vision and Pattern Recognition" in res["final_response"]
        assert res["verification_summary"]["final_status"] == "verified"
        assert res["verification_summary"]["unresolved_count"] == 0


# ==============================================================================
# SCENARIO F: Similar Titles Belonging to Different Publications
# ==============================================================================
def test_scenario_f_similar_titles_different_publications():
    """
    F. Similar titles belonging to different publications are distinguished by authors
    and never adopted as false positive matches.
    """
    citation = """Title: Deep Residual Learning for Image Recognition
Authors: Kaiming He, Xiangyu Zhang, Shaoqing Ren, Jian Sun
Year: 2016"""

    distractor_paper = {
        "title": "Deep Residual Learning for Compressed Image Restoration",
        "authors": ["Yuesheng Zhu", "Ke Zheng", "Hongwei Liu"],
        "year": 2017,
        "venue": "IEEE Access",
        "doi": "10.1109/ACCESS.2017.2764832",
        "source": "Crossref",
    }

    with patch("app.services.verification_pipeline.retrieve_candidates", return_value=[distractor_paper]), \
         patch("app.services.crossref_service.verify_doi", return_value=None):

        results = verify_response(citation)
        assert len(results) == 1
        r = results[0]

        # Author similarity is low, paper should not be verified as existing through this distractor
        assert r["author_similarity"] < 40
        assert r["citation_accurate"] is False


# ==============================================================================
# SCENARIO G: arXiv Preprint and Related Conference Publication
# ==============================================================================
def test_scenario_g_arxiv_preprint_and_conference_compatibility():
    """
    G. An arXiv preprint and its related conference publication.
    Verifies venue compatibility between NeurIPS and arXiv.
    """
    from app.services.similarity_service import compare_venues

    # Advances in Neural Information Processing Systems and arXiv
    match, score = compare_venues(
        "Advances in Neural Information Processing Systems",
        "arXiv",
        use_venue_fix=True
    )
    assert match is True
    assert score >= 90.0

    # CVPR and arXiv
    match_cvpr, score_cvpr = compare_venues("CVPR", "arXiv", use_venue_fix=True)
    assert match_cvpr is True
    assert score_cvpr >= 90.0


# ==============================================================================
# SCENARIO H: Conflicting or Incomplete Metadata Across Sources
# ==============================================================================
def test_scenario_h_conflicting_incomplete_metadata_reconciliation():
    """
    H. Conflicting or incomplete metadata across sources reconciled safely.
    Crossref has partial authors (2) and later reprint year (2025).
    DataCite has full authors (8) and original discovery year (2017).
    Merged candidate must retain 8 authors, 2017 year, and full provenance.
    """
    from app.services.multi_source_retriever import retrieve_candidates

    cr_mock = [{
        "title": "Attention Is All You Need",
        "authors": ["Ashish Vaswani", "Noam Shazeer"],
        "year": 2025,
        "venue": "",
        "doi": "10.65215/ysbyhc05",
        "source": "Crossref",
    }]

    dc_mock = [{
        "title": "Attention Is All You Need",
        "authors": [
            "Ashish Vaswani", "Noam Shazeer", "Niki Parmar", "Jakob Uszkoreit",
            "Llion Jones", "Aidan N. Gomez", "Lukasz Kaiser", "Illia Polosukhin"
        ],
        "year": 2017,
        "alternate_years": [2017],
        "venue": "arXiv",
        "doi": "10.48550/arxiv.1706.03762",
        "source": "DataCite",
    }]

    from app.services.candidate_ranker import rank_candidates

    with patch("app.services.crossref_service.verify_title", return_value=cr_mock), \
         patch("app.services.semantic_scholar_service.search_semantic_scholar", return_value=[]), \
         patch("app.services.openalex_service.search_openalex", return_value=[]), \
         patch("app.services.datacite_service.search_datacite", return_value=dc_mock):

        candidates = retrieve_candidates("Attention Is All You Need", authors=["Ashish Vaswani"])
        assert len(candidates) >= 1

        # Candidate ranker selects the primary original 2017 publication with full authors
        ranked = rank_candidates(
            {"title": "Attention Is All You Need", "year": 2017, "authors": ["Ashish Vaswani"]},
            candidates
        )
        assert len(ranked) >= 1
        best = ranked[0]["paper"]

        # Year reconciled to primary original year
        assert best["year"] == 2017
        # Full 8 authors retained
        assert len(best["authors"]) == 8
        # Canonical arXiv DOI prioritized over mirror
        assert best["doi"] == "10.48550/arxiv.1706.03762"
        # Provenance retained
        assert "DataCite" in best["provenance"]["sources_corroborating"]


# ==============================================================================
# SCENARIO I: External API Timeout or Rate Limit Graceful Handling
# ==============================================================================
def test_scenario_i_api_timeout_or_rate_limit_graceful_handling():
    """
    I. External API timeout or rate limit handled gracefully.
    When all providers fail or time out, pipeline handles telemetry and returns unverified cleanly.
    """
    from app.services import crossref_service, semantic_scholar_service, openalex_service, datacite_service

    with patch("app.services.crossref_service.verify_title", return_value=[]), \
         patch("app.services.semantic_scholar_service.search_semantic_scholar", return_value=[]), \
         patch("app.services.openalex_service.search_openalex", return_value=[]), \
         patch("app.services.datacite_service.search_datacite", return_value=[]), \
         patch.dict(crossref_service.last_status, {"success": False, "error": "Timeout"}), \
         patch.dict(semantic_scholar_service.last_status, {"success": False, "error": "HTTP 429"}), \
         patch.dict(openalex_service.last_status, {"success": False, "error": "Timeout"}), \
         patch.dict(datacite_service.last_status, {"success": False, "error": "Timeout"}):

        citation = "1. Nonexistent Paper by Anonymous, 2023"
        res = correct_and_reverify_response(citation, max_iterations=2)

        assert res["verification_summary"]["final_status"] == "unverified"
        assert res["verification_summary"]["unresolved_count"] >= 1


# ==============================================================================
# SCENARIO J: Correction Cannot Be Resolved Confidently -> Needs Review
# ==============================================================================
def test_scenario_j_unresolved_correction_transparently_qualified():
    """
    J. A correction that cannot be resolved confidently.
    Preserves unresolved state, transparently qualifies citation, and does not claim verified.
    """
    citation = """Title: "Hallucinated Architecture for Instant Superintelligence"
Authors: Unknown Author
Year: 2026
DOI: 10.9999/hallucinated.doi"""

    with patch("app.main.classify_prompt", return_value={"label": 0, "label_name": "Safe", "confidence": 0.95}), \
         patch("app.services.verification_pipeline.verify_doi", return_value=None), \
         patch("app.services.verification_pipeline.retrieve_candidates", return_value=[]):

        res = correct_and_reverify_response(citation, max_iterations=2)

        assert res["verification_summary"]["final_status"] in ["unverified", "correction_failed"]
        assert res["verification_summary"]["unresolved_count"] >= 1
        assert ("UNVERIFIED REFERENCE" in res["final_response"] or "Warning: Claim-to-source mismatch" in res["final_response"])


# ==============================================================================
# SCENARIO K: Multiple Citations with Mixture of Valid and Unresolved Records
# ==============================================================================
def test_scenario_k_multiple_citations_mixed_valid_and_unresolved():
    """
    K. Multiple citations with a mixture of valid and unresolved records.
    Citation 1 is verified; Citation 2 is unverified.
    Expected overall status: partially_verified, verified_count: 1, unresolved_count: 1.
    """
    text = """1. Deep Residual Learning for Image Recognition
Authors: Kaiming He, Xiangyu Zhang, Shaoqing Ren, Jian Sun
Year: 2016
Venue: CVPR
DOI: 10.1109/CVPR.2016.90

2. Completely Fabricated Study on Teleportation
Authors: Dr. Imaginary
Year: 2025"""

    mock_c1 = {
        "citation": "1. Deep Residual Learning for Image Recognition...",
        "paper_exists": True,
        "citation_accurate": True,
        "hallucination_type": "Valid Citation",
        "metadata_errors": [],
        "matched_title": "Deep Residual Learning for Image Recognition",
        "matched_authors": ["Kaiming He", "Xiangyu Zhang", "Shaoqing Ren", "Jian Sun"],
        "matched_year": 2016,
        "matched_venue": "CVPR",
        "matched_doi": "10.1109/CVPR.2016.90",
        "hallucination_score": 0,
        "confidence": "Verified Citation",
    }

    mock_c2 = {
        "citation": "2. Completely Fabricated Study on Teleportation...",
        "paper_exists": False,
        "citation_accurate": False,
        "hallucination_type": "Fabricated Citation",
        "metadata_errors": ["Paper not found"],
        "matched_title": None,
        "matched_authors": [],
        "matched_year": None,
        "matched_venue": None,
        "matched_doi": None,
        "hallucination_score": 100,
        "confidence": "High Risk of Hallucination",
    }

    def mock_verifier(t, **kwargs):
        return [dict(mock_c1), dict(mock_c2)]

    res = correct_and_reverify_response(text, max_iterations=1, verifier=mock_verifier)

    assert res["verification_summary"]["final_status"] == "partially_verified"
    assert res["verification_summary"]["total_citations"] == 2
    assert res["verification_summary"]["verified_count"] == 1
    assert res["verification_summary"]["unresolved_count"] == 1


# ==============================================================================
# SCENARIO L: Invariant Check: Unresolved Discrepancies Cannot Be Verified
# ==============================================================================
def test_scenario_l_invariant_no_false_verification_with_discrepancies():
    """
    L. An invariant ensuring that known final metadata discrepancies cannot be reported as fully verified.
    If unresolved_count > 0, final_status CANNOT be 'verified'.
    """
    text = "Title: Mismatched Citation"
    mock_failing_result = [{
        "citation": text,
        "paper_exists": True,
        "citation_accurate": False,
        "hallucination_type": "Metadata Hallucination",
        "metadata_errors": ["DOI mismatch"],
        "matched_title": "Some Paper",
        "matched_authors": ["Author"],
        "matched_year": 2020,
        "matched_venue": "Venue",
        "matched_doi": "10.1234/real",
        "hallucination_score": 30,
        "confidence": "Paper Exists but Citation Contains Errors",
    }]

    with patch("app.services.correction_service.verify_response", return_value=mock_failing_result):
        res = correct_and_reverify_response(text, max_iterations=2)

        summary = res["verification_summary"]
        assert summary["unresolved_count"] >= 1
        assert summary["final_status"] != "verified"
        assert summary["final_status"] in ["correction_failed", "unverified", "partially_verified"]


# ==============================================================================
# SECTION: COMPREHENSIVE 17-CASE REGRESSION SUITE (SPECIFICATION SECTION 9)
# ==============================================================================

# Case 1: Completely fabricated citation with fabricated DOI
def test_regression_01_completely_fabricated_citation_with_fabricated_doi():
    citation = """Title: Neuro-Symbolic Dream Synthesizer via Quantum Entanglement
Authors: Dr. Imaginary, Prof. Fictional
Year: 2025
Venue: Journal of Impossible Science
DOI: 10.9999/fabricated.2025.12345"""

    with patch("app.main.classify_prompt", return_value={"label": 0, "label_name": "Safe", "confidence": 0.95}), \
         patch("app.services.verification_pipeline.verify_doi", return_value=None), \
         patch("app.services.verification_pipeline.retrieve_candidates", return_value=[]):

        res = correct_and_reverify_response(citation, max_iterations=2)
        assert res["verification_summary"]["final_status"] in ["unverified", "correction_failed"]
        assert res["verification_summary"]["unresolved_count"] == 1
        assert res["verification_summary"]["verified_count"] == 0
        assert "UNVERIFIED REFERENCE" in res["final_response"]


# Case 2: The exact fabricated dream citation and financial-paper distractor
def test_regression_02_exact_dream_paper_financial_distractor_never_substituted():
    citation = """Title: Quantum-Enhanced Deep Learning for Predicting Human Dreams
Authors: Alex Morgan, Priya Sharma, Daniel Wilson
Year: 2024
Venue: International Journal of Neural Dream Computing
DOI: 10.5555/fictional.2024.987654"""

    unrelated_financial_distractor = {
        "title": "Quantum-Enhanced Deep Learning for Financial Anomaly Detection",
        "authors": ["Rayane Aggoune", "Abdelhak Merizig"],
        "year": 2026,
        "venue": "Advances in Economics, Business and Management Research",
        "doi": "10.2991/978-94-6239-711-8_9",
        "source": "Crossref",
    }

    with patch("app.services.verification_pipeline.retrieve_candidates", return_value=[unrelated_financial_distractor]), \
         patch("app.services.crossref_service.verify_doi", return_value=None), \
         patch("app.services.datacite_service.verify_datacite_doi", return_value=None):

        res = correct_and_reverify_response(citation, max_iterations=2)

        # 1. Must not claim verified
        assert res["verification_summary"]["final_status"] != "verified"
        assert res["verification_summary"]["final_status"] in ["unverified", "correction_failed"]
        assert res["verification_summary"]["unresolved_count"] == 1
        assert res["verification_summary"]["verified_count"] == 0

        # 2. Financial paper rejected as replacement
        assert "Financial Anomaly Detection" not in res["final_response"]
        assert "Rayane Aggoune" not in res["final_response"]
        assert "10.2991" not in res["final_response"]

        # 3. Original title and author metadata preserved in audit and response
        assert "Predicting Human Dreams" in res["final_response"]
        assert "Alex Morgan" in res["final_response"]
        assert "UNVERIFIED REFERENCE" in res["final_response"]


# Case 3: Real paper with incorrect DOI
def test_regression_03_real_paper_incorrect_doi_corrected_and_verified():
    citation = """1. Deep Residual Learning for Image Recognition
Authors: Kaiming He, Xiangyu Zhang, Shaoqing Ren, Jian Sun
Year: 2016
Venue: CVPR
DOI: 10.1038/nature12345"""

    resnet_canonical = {
        "title": "Deep Residual Learning for Image Recognition",
        "authors": ["Kaiming He", "Xiangyu Zhang", "Shaoqing Ren", "Jian Sun"],
        "year": 2016,
        "venue": "CVPR",
        "doi": "10.1109/CVPR.2016.90",
        "source": "Crossref",
    }
    unrelated_nature = {
        "title": "Unrelated Nature Article",
        "authors": ["A. Nonymous"],
        "year": 2013,
        "venue": "Nature",
        "doi": "10.1038/nature12345",
        "source": "Crossref",
    }

    def mock_doi(doi):
        return unrelated_nature if "nature12345" in str(doi) else resnet_canonical

    with patch("app.services.verification_pipeline.retrieve_candidates", return_value=[resnet_canonical]), \
         patch("app.services.crossref_service.verify_doi", side_effect=mock_doi):

        res = correct_and_reverify_response(citation, max_iterations=2)
        assert res["verification_summary"]["final_status"] == "verified"
        assert res["verification_summary"]["unresolved_count"] == 0
        assert res["verification_summary"]["verified_count"] == 1
        assert "10.1109/CVPR.2016.90" in res["final_response"]
        assert "10.1038/nature12345" not in res["final_response"]


# Case 4: A real DOI belonging to a different publication
def test_regression_04_real_doi_belonging_to_different_publication_rejected():
    citation = """Title: Quantum Machine Learning for Protein Folding
Authors: Jane Doe, Alice Smith
Year: 2024
DOI: 10.1038/s41586-020-2649-2"""

    numpy_paper = {
        "title": "Array programming with NumPy",
        "authors": ["Charles R. Harris", "K. Jarrod Millman"],
        "year": 2020,
        "venue": "Nature",
        "doi": "10.1038/s41586-020-2649-2",
        "source": "Crossref",
    }

    with patch("app.services.verification_pipeline.retrieve_candidates", return_value=[]), \
         patch("app.services.crossref_service.verify_doi", return_value=numpy_paper):

        res = correct_and_reverify_response(citation, max_iterations=2)
        assert res["verification_summary"]["final_status"] in ["unverified", "correction_failed"]
        assert res["verification_summary"]["unresolved_count"] >= 1
        assert "Array programming with NumPy" not in res["final_response"]
        assert "UNVERIFIED REFERENCE" in res["final_response"]


# Case 5: Correct DOI but conflicting title
def test_regression_05_correct_doi_but_conflicting_title_rejected():
    citation = """Title: Completely Fabricated Title on Planetary Dynamics
Authors: Jane Doe, Alice Smith
Year: 2016
DOI: 10.1109/CVPR.2016.90"""

    resnet_paper = {
        "title": "Deep Residual Learning for Image Recognition",
        "authors": ["Kaiming He", "Xiangyu Zhang", "Shaoqing Ren", "Jian Sun"],
        "year": 2016,
        "venue": "CVPR",
        "doi": "10.1109/CVPR.2016.90",
        "source": "Crossref",
    }

    with patch("app.services.verification_pipeline.retrieve_candidates", return_value=[]), \
         patch("app.services.crossref_service.verify_doi", return_value=resnet_paper):

        res = correct_and_reverify_response(citation, max_iterations=2)
        assert res["verification_summary"]["final_status"] != "verified"
        assert res["verification_summary"]["unresolved_count"] >= 1
        assert "Deep Residual Learning for Image Recognition" not in res["final_response"]
        assert "UNVERIFIED REFERENCE" in res["final_response"]


# Case 6: Correct title but conflicting authors
def test_regression_06_correct_title_but_conflicting_authors_detected():
    citation = """Title: Attention Is All You Need
Authors: John Smith, David Jones
Year: 2017
Venue: NeurIPS"""

    transformer_paper = {
        "title": "Attention Is All You Need",
        "authors": ["Ashish Vaswani", "Noam Shazeer", "Niki Parmar", "Jakob Uszkoreit"],
        "year": 2017,
        "venue": "Advances in Neural Information Processing Systems",
        "doi": "10.48550/arXiv.1706.03762",
        "source": "Crossref",
    }

    with patch("app.services.verification_pipeline.retrieve_candidates", return_value=[transformer_paper]), \
         patch("app.services.crossref_service.verify_doi", return_value=transformer_paper):

        res = correct_and_reverify_response(citation, max_iterations=2)
        # Because authors conflict completely (<40%), candidate viability rejects it as unverified
        assert res["verification_summary"]["final_status"] != "verified"
        assert res["verification_summary"]["unresolved_count"] >= 1
        assert "UNVERIFIED REFERENCE" in res["final_response"]


# Case 7: Similar title with conflicting authors and publication year
def test_regression_07_similar_title_conflicting_authors_and_year_prioritizes_match():
    from app.services.candidate_ranker import rank_candidates

    parsed = {
        "title": "Survey on Deep Learning for Healthcare",
        "authors": ["Alice Brown", "Charlie Green"],
        "year": 2021,
    }
    cand_distractor = {
        "title": "Survey on Deep Learning for Healthcare",
        "authors": ["John Smith", "David Lee"],
        "year": 2023,
        "doi": "10.1109/distractor",
        "source": "Crossref",
    }
    cand_target = {
        "title": "Survey on Deep Learning for Healthcare",
        "authors": ["Alice Brown", "Charlie Green"],
        "year": 2021,
        "doi": "10.1109/target",
        "source": "Crossref",
    }

    ranked = rank_candidates(parsed, [cand_distractor, cand_target])
    assert len(ranked) == 2
    assert ranked[0]["paper"]["doi"] == "10.1109/target"
    assert ranked[0]["final_score"] > ranked[1]["final_score"]


# Case 8: Minor title-formatting differences
def test_regression_08_minor_title_formatting_differences_verified():
    citation = """Title: “deep residual learning for image recognition”
Authors: Kaiming He, Xiangyu Zhang, Shaoqing Ren, Jian Sun
Year: 2016
Venue: CVPR
DOI: 10.1109/CVPR.2016.90"""

    resnet_paper = {
        "title": "Deep Residual Learning for Image Recognition",
        "authors": ["Kaiming He", "Xiangyu Zhang", "Shaoqing Ren", "Jian Sun"],
        "year": 2016,
        "venue": "CVPR",
        "doi": "10.1109/CVPR.2016.90",
        "source": "Crossref",
    }

    with patch("app.services.verification_pipeline.retrieve_candidates", return_value=[resnet_paper]), \
         patch("app.services.crossref_service.verify_doi", return_value=resnet_paper):

        res = correct_and_reverify_response(citation, max_iterations=2)
        assert res["verification_summary"]["final_status"] == "verified"
        assert res["verification_summary"]["unresolved_count"] == 0
        assert res["verification_summary"]["verified_count"] == 1


# Case 9: Legitimate preprint and published-version relationship
def test_regression_09_legitimate_preprint_and_published_version_compatibility():
    from app.services.similarity_service import compare_venues

    is_match, score = compare_venues(
        "Advances in Neural Information Processing Systems",
        "arXiv",
        use_venue_fix=True,
    )
    assert is_match is True
    assert score >= 90.0


# Case 10: Empty, unavailable, timed-out, or conflicting provider results
def test_regression_10_empty_unavailable_timed_out_provider_responses_graceful():
    from app.services import crossref_service, semantic_scholar_service, openalex_service, datacite_service

    citation = """Title: Any Scientific Publication
Authors: Some Scientist
Year: 2023"""

    with patch("app.services.crossref_service.verify_title", return_value=[]), \
         patch("app.services.semantic_scholar_service.search_semantic_scholar", return_value=[]), \
         patch("app.services.openalex_service.search_openalex", return_value=[]), \
         patch("app.services.datacite_service.search_datacite", return_value=[]), \
         patch.dict(crossref_service.last_status, {"success": False, "error": "HTTP 503 Outage"}), \
         patch.dict(semantic_scholar_service.last_status, {"success": False, "error": "HTTP 503 Outage"}), \
         patch.dict(openalex_service.last_status, {"success": False, "error": "HTTP 503 Outage"}), \
         patch.dict(datacite_service.last_status, {"success": False, "error": "HTTP 503 Outage"}):

        res = correct_and_reverify_response(citation, max_iterations=2)
        assert res["verification_summary"]["final_status"] == "unverified"
        assert res["verification_summary"]["unresolved_count"] == 1
        assert res["verification_summary"]["verified_count"] == 0
        assert "UNVERIFIED REFERENCE" in res["final_response"]


# Case 11: Genuine candidate with insufficient evidence of identity
def test_regression_11_genuine_candidate_insufficient_evidence_unverified():
    citation = """Title: Deep Learning Architectures for Autonomous Underwater Navigation
Authors: Sandra Martinez, Liam O'Connor
Year: 2024
Venue: Ocean Robotics Journal"""

    weak_distractor = {
        "title": "Deep Learning for Satellite Weather Forecasting",
        "authors": ["Zhiqiang Wang", "Hong Li"],
        "year": 2018,
        "venue": "Atmospheric Research",
        "doi": "10.1016/j.atmosres.2018.01.002",
        "source": "Crossref",
    }

    with patch("app.services.verification_pipeline.retrieve_candidates", return_value=[weak_distractor]), \
         patch("app.services.crossref_service.verify_doi", return_value=None):

        res = correct_and_reverify_response(citation, max_iterations=2)
        assert res["verification_summary"]["final_status"] in ["unverified", "correction_failed"]
        assert res["verification_summary"]["unresolved_count"] == 1
        assert "Satellite Weather Forecasting" not in res["final_response"]
        assert "UNVERIFIED REFERENCE" in res["final_response"]


# Case 12: Correction that remains unresolved after the maximum iteration count
def test_regression_12_correction_unresolved_after_max_iterations_fails_truthfully():
    flawed_text = """1. Flawed Citation Title
Authors: Wrong Authors
Year: 2020"""

    unresolvable_result = [{
        "citation": flawed_text,
        "paper_exists": True,
        "citation_accurate": False,
        "metadata_errors": ["Author mismatch"],
        "matched_title": "Flawed Citation Title",
        "matched_authors": ["Right Author One", "Right Author Two"],
        "matched_year": 2020,
        "matched_venue": None,
        "matched_doi": None,
        "matched_abstract": "Some abstract.",
        "hallucination_score": 40,
        "confidence": "Paper Exists but Citation Contains Errors",
        "author_similarity": 10.0,
        "title_similarity": 100.0,
        "year_match": True,
        "venue_match": True,
        "doi_match": False,
    }]

    with patch("app.services.correction_service.verify_response", return_value=unresolvable_result):
        res = correct_and_reverify_response(flawed_text, max_iterations=2)
        assert res["verification_summary"]["unresolved_count"] >= 1
        assert res["verification_summary"]["final_status"] != "verified"
        assert res["verification_summary"]["final_status"] in ["correction_failed", "unverified", "partially_verified"]


# Case 13: Second verification that finds a different genuine publication
def test_regression_13_second_verification_finding_different_paper_cannot_erase_unresolved():
    fake_citation = """Title: Fabricated Study On Mind Reading
Authors: John Doe
Year: 2025"""

    fake_result = [{
        "citation": fake_citation,
        "paper_exists": False,
        "citation_accurate": False,
        "hallucination_type": "Fabricated Citation",
        "metadata_errors": ["Paper not found"],
        "matched_title": None,
        "matched_authors": [],
        "matched_year": None,
        "matched_venue": None,
        "matched_doi": None,
    }]

    with patch("app.services.correction_service.verify_response", return_value=fake_result):
        res = correct_and_reverify_response(fake_citation, max_iterations=2)
        assert res["verification_summary"]["final_status"] != "verified"
        assert res["verification_summary"]["unresolved_count"] == 1
        assert "UNVERIFIED REFERENCE" in res["final_response"]


# Case 14: Multiple citations where some are verified and others remain unresolved
def test_regression_14_multiple_citations_mixed_verified_and_unresolved():
    text = """1. Deep Residual Learning for Image Recognition
Authors: Kaiming He, Xiangyu Zhang, Shaoqing Ren, Jian Sun
Year: 2016
Venue: CVPR
DOI: 10.1109/CVPR.2016.90

2. Completely Fabricated Study on Teleportation
Authors: Dr. Imaginary
Year: 2025"""

    mock_c1 = {
        "citation": "1. Deep Residual Learning for Image Recognition...",
        "paper_exists": True,
        "citation_accurate": True,
        "hallucination_type": "Valid Citation",
        "metadata_errors": [],
        "matched_title": "Deep Residual Learning for Image Recognition",
        "matched_authors": ["Kaiming He", "Xiangyu Zhang", "Shaoqing Ren", "Jian Sun"],
        "matched_year": 2016,
        "matched_venue": "CVPR",
        "matched_doi": "10.1109/CVPR.2016.90",
        "hallucination_score": 0,
        "confidence": "Verified Citation",
    }
    mock_c2 = {
        "citation": "2. Completely Fabricated Study on Teleportation...",
        "paper_exists": False,
        "citation_accurate": False,
        "hallucination_type": "Fabricated Citation",
        "metadata_errors": ["Paper not found"],
        "matched_title": None,
        "matched_authors": [],
        "matched_year": None,
        "matched_venue": None,
        "matched_doi": None,
        "hallucination_score": 100,
        "confidence": "High Risk of Hallucination",
    }

    def mock_verifier(t, **kwargs):
        return [dict(mock_c1), dict(mock_c2)]

    res = correct_and_reverify_response(text, max_iterations=1, verifier=mock_verifier)
    assert res["verification_summary"]["final_status"] == "partially_verified"
    assert res["verification_summary"]["total_citations"] == 2
    assert res["verification_summary"]["verified_count"] == 1
    assert res["verification_summary"]["unresolved_count"] == 1


# Case 15: API serialization and frontend status mapping
def test_regression_15_api_serialization_and_frontend_status_mapping():
    from app.main import analyze, PromptRequest

    fake_text = """Title: Quantum-Enhanced Deep Learning for Predicting Human Dreams
Authors: Alex Morgan, Priya Sharma, Daniel Wilson
Year: 2024
Venue: International Journal of Neural Dream Computing
DOI: 10.5555/fictional.2024.987654"""

    mock_workflow = {
        "original_response": fake_text,
        "final_response": fake_text + "\nNote: [UNVERIFIED REFERENCE: Referenced paper could not be verified in Crossref, Semantic Scholar, or OpenAlex. This citation may be hallucinated or incorrect.]",
        "initial_citation_analysis": [{
            "citation": fake_text,
            "paper_exists": False,
            "citation_accurate": False,
            "hallucination_type": "Fabricated Citation",
            "metadata_errors": ["Paper not found"],
        }],
        "final_citation_analysis": [{
            "citation": fake_text,
            "paper_exists": False,
            "citation_accurate": False,
            "hallucination_type": "Fabricated Citation",
            "metadata_errors": ["Paper not found"],
        }],
        "applied_corrections": [{
            "original_citation": fake_text,
            "corrected_citation": fake_text + "\nNote: [UNVERIFIED REFERENCE...]",
            "correction_type": "transparent_qualification",
            "verified_in_next_step": False,
        }],
        "verification_summary": {
            "final_status": "unverified",
            "total_citations": 1,
            "verified_count": 0,
            "corrected_and_verified_count": 0,
            "unresolved_count": 1,
            "iterations_run": 1,
            "limitations": "1 citation(s) could not be verified in authoritative scholarly registries.",
        },
        "audit_trail": [],
    }

    with patch("app.main.classify_prompt", return_value={"label": 0, "label_name": "Safe", "confidence": 0.95}), \
         patch("app.main.correct_and_reverify_response", return_value=mock_workflow):

        data = analyze(PromptRequest(prompt="test", llm_response=fake_text))

        # Contract checks for frontend rendering
        summary = data["verification_summary"]
        assert summary["final_status"] == "unverified"
        assert summary["unresolved_count"] == 1
        assert summary["final_status"] != "verified"

        # Citations array checks
        assert len(data["citation_analysis"]) == 1
        c0 = data["citation_analysis"][0]
        assert c0["paper_exists"] is False
        assert c0["citation_accurate"] is False
        assert "UNVERIFIED REFERENCE" in data["final_response"]


# Case 16: Metadata supported but claim-to-source evidence insufficient
def test_regression_16_metadata_supported_but_claim_to_source_evidence_insufficient():
    paper_record = {
        "paper_exists": True,
        "matched_title": "Novel Quantum Algorithm For Sorting",
        "matched_abstract": None,
    }

    claim = "This algorithm sorts arbitrary integers in O(1) quantum steps."
    res = verify_claim_support(claim, paper_record)

    assert res["status"] == "insufficient_evidence"
    assert res["supported"] is None
    assert "public registries" in res["reason"]


# Case 17: Repeated requests to ensure previous results do not contaminate the next request
def test_regression_17_repeated_requests_prevent_cross_contamination():
    citation_fake = """Title: Fake Paper
Authors: Fake Author
Year: 2025"""
    citation_real = """Title: Real ResNet Paper
Authors: Kaiming He
Year: 2016"""

    mock_fake = [{
        "citation": citation_fake,
        "paper_exists": False,
        "citation_accurate": False,
        "hallucination_type": "Fabricated Citation",
        "metadata_errors": ["Paper not found"],
        "matched_title": None,
        "matched_authors": [],
        "matched_year": None,
        "matched_venue": None,
        "matched_doi": None,
    }]
    mock_real = [{
        "citation": citation_real,
        "paper_exists": True,
        "citation_accurate": True,
        "hallucination_type": "Valid Citation",
        "metadata_errors": [],
        "matched_title": "Real ResNet Paper",
        "matched_authors": ["Kaiming He"],
        "matched_year": 2016,
        "matched_venue": "CVPR",
        "matched_doi": "10.1109/CVPR.2016.90",
    }]

    with patch("app.services.correction_service.verify_response", side_effect=[mock_fake, mock_real]):
        res1 = correct_and_reverify_response(citation_fake, max_iterations=1)
        res2 = correct_and_reverify_response(citation_real, max_iterations=1)

        assert res1["verification_summary"]["final_status"] != "verified"
        assert res1["verification_summary"]["unresolved_count"] == 1

        assert res2["verification_summary"]["final_status"] == "verified"
        assert res2["verification_summary"]["unresolved_count"] == 0
        assert "Fake Paper" not in res2["final_response"]


# ==============================================================================
# PROVIDER OUTAGE & UNAVAILABLE EVIDENCE REGRESSION TESTS
# ==============================================================================

def test_regression_18_provider_outage_http_503_unverified_not_fabricated():
    """
    When all scholarly metadata providers return HTTP 503:
    1. The application does not crash and does not invent a replacement citation.
    2. Provider unavailability is NOT treated as proof that the paper is fabricated (paper_exists is None, not False).
    3. The hallucination_type is 'Unverified / Provider Outage', not 'Fabricated Citation'.
    4. The citation cannot be marked VERIFIED; final_status must be 'unverified'.
    5. unresolved_count is 1, verified_count is 0.
    6. Transparent qualification note is attached indicating external APIs were unreachable.
    7. Claim verification reports 'insufficient_evidence', not 'unsupported_claim'.
    """
    mock_resp_503 = MagicMock()
    mock_resp_503.status_code = 503
    mock_resp_503.json.return_value = {}

    citation_text = (
        'Recent distributed systems research: [1] Sarah Jenkins and Michael Chang, '
        '"Scalable Byzantine Consensus in Asynchronous Networks", ACM Transactions on Computer Systems, 2023. '
        'DOI: 10.1145/3581234.3585678.'
    )

    with patch("app.services.cache_service.session.get", return_value=mock_resp_503):
        res = correct_and_reverify_response(citation_text, verifier=verify_response, max_iterations=2)

        # 1. No crash, summary assertions
        summary = res["verification_summary"]
        assert summary["final_status"] == "unverified"
        assert summary["final_status"] != "verified"
        assert summary["verified_count"] == 0
        assert summary["unresolved_count"] == 1
        assert "unreachable" in summary["limitations"].lower() or "rate limit" in summary["limitations"].lower()

        # 2. Check re-verified citation details
        final_citations = res["final_citation_analysis"]
        assert len(final_citations) == 1
        c = final_citations[0]

        # Invariant: provider outage is NOT proof of fabrication
        assert c["paper_exists"] is None
        assert c["paper_exists"] is not False
        assert c["citation_accurate"] is False
        assert c["hallucination_type"] == "Unverified / Provider Outage"
        assert c["api_status"] == "OUTAGE"

        # 3. Check response text: no replacement citation invented, transparent qualification attached
        final_text = res["final_response"]
        assert "Scalable Byzantine Consensus in Asynchronous Networks" in final_text
        assert "UNVERIFIED REFERENCE: External scholarly APIs were unreachable" in final_text

        # 4. Claim verification handles unavailable evidence truthfully
        claim_ver = c.get("claim_verification")
        assert claim_ver["status"] == "insufficient_evidence"
        assert claim_ver["supported"] is None


def test_regression_19_provider_timeout_unverified_and_resilient():
    """
    When all providers time out (requests.exceptions.Timeout):
    - Handled gracefully without raising unhandled exceptions
    - paper_exists is None (not treated as fabricated)
    - final_status is 'unverified'
    - verified_count is 0, unresolved_count is 1
    """
    import requests

    citation_text = (
        'Cognitive computing: [1] Elena Rostova, "Sparse Representations in Spiking Neural Networks", '
        'Journal of Neural Computation, 2022. DOI: 10.1162/neco_a_01456.'
    )

    with patch("app.services.cache_service.session.get", side_effect=requests.exceptions.Timeout("Connection timed out")):
        res = correct_and_reverify_response(citation_text, verifier=verify_response, max_iterations=2)

        summary = res["verification_summary"]
        assert summary["final_status"] == "unverified"
        assert summary["final_status"] != "verified"
        assert summary["verified_count"] == 0
        assert summary["unresolved_count"] == 1

        c = res["final_citation_analysis"][0]
        assert c["paper_exists"] is None
        assert c["paper_exists"] is not False
        assert c["hallucination_type"] == "Unverified / Provider Outage"
        assert "UNVERIFIED REFERENCE" in res["final_response"]


def test_regression_20_healthy_providers_empty_results_distinguished_from_outage():
    """
    When providers are healthy (HTTP 200) but return empty lists (paper not found):
    - Confirmed negative evidence IS treated as paper not found (paper_exists is False)
    - hallucination_type is 'Fabricated Citation' (unlike provider outage where paper_exists is None)
    - final_status is correction_failed or unverified, never verified
    - unresolved_count is 1
    """
    mock_resp_empty = MagicMock()
    mock_resp_empty.status_code = 200
    mock_resp_empty.json.return_value = {"message": {"items": []}, "data": []}

    citation_text = (
        'Synthetic citation:\n[1] Nonexistent Author, "Fictitious Manuscript On Imaginary Algorithms", '
        'Imaginary Press, 2025.'
    )

    with patch("app.services.cache_service.session.get", return_value=mock_resp_empty), \
         patch("app.services.semantic_scholar_service.search_semantic_scholar", return_value=[]), \
         patch("app.services.openalex_service.search_openalex", return_value=[]), \
         patch("app.services.datacite_service.search_datacite", return_value=[]):

        res = correct_and_reverify_response(citation_text, verifier=verify_response, max_iterations=2)

        summary = res["verification_summary"]
        assert summary["final_status"] != "verified"
        assert summary["unresolved_count"] == 1

        c = res["final_citation_analysis"][0]
        assert c["paper_exists"] is False  # Confirmed negative evidence
        assert c["hallucination_type"] == "Fabricated Citation"


def test_regression_21_end_to_end_analyze_endpoint_provider_outage_contract():
    """
    End-to-end /analyze API test with simulated provider outage.
    Verifies that the API response contract received by the frontend:
    - Sets final_status to 'unverified' (rendered as 'UNVERIFIED — INSUFFICIENT EVIDENCE / REGISTRY OUTAGE')
    - Has verified_count = 0, unresolved_count = 1
    - Sets paper_exists = None and hallucination_type = 'Unverified / Provider Outage'
    - Prevents false positive success display on frontend
    """
    from app.main import analyze, PromptRequest

    mock_resp_503 = MagicMock()
    mock_resp_503.status_code = 503
    mock_resp_503.json.return_value = {}

    citation_input = (
        'Distributed systems:\n[1] David Miller, "Consensus Under Network Partitions", IEEE TDSC, 2021.'
    )

    with patch("app.main.classify_prompt", return_value={"label": 0, "label_name": "Safe", "confidence": 0.99}), \
         patch("app.services.cache_service.session.get", return_value=mock_resp_503):

        response_payload = analyze(PromptRequest(prompt="Explain consensus", llm_response=citation_input))

        summary = response_payload["verification_summary"]
        assert summary["final_status"] == "unverified"
        assert summary["final_status"] != "verified"
        assert summary["verified_count"] == 0
        assert summary["unresolved_count"] == 1

        citations = response_payload["citation_analysis"]
        assert len(citations) == 1
        assert citations[0]["paper_exists"] is None
        assert citations[0]["citation_accurate"] is False
        assert citations[0]["hallucination_type"] == "Unverified / Provider Outage"
        assert citations[0]["api_status"] == "OUTAGE"
        assert "UNVERIFIED REFERENCE" in response_payload["final_response"]
