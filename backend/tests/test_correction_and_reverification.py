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
        assert "UNVERIFIED REFERENCE" in res["final_response"]


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
# SCENARIO 6: A relevant replacement source is found and verified.
# ==============================================================================
def test_06_relevant_replacement_source_found_and_verified():
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

    genuine_replacement = {
        "title": "Deep Residual Learning for Image Recognition",
        "authors": ["Kaiming He", "Xiangyu Zhang", "Shaoqing Ren", "Jian Sun"],
        "year": 2016,
        "venue": "CVPR",
        "doi": "10.1109/CVPR.2016.90",
        "abstract": "Deeper neural networks are more difficult to train. We present a residual learning framework.",
    }

    verified_rep_result = [{
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

    with patch("app.services.correction_service.verify_response", side_effect=[fake_result, verified_rep_result]), \
         patch("app.services.correction_service.search_replacement_paper", return_value=genuine_replacement):
        res = correct_and_reverify_response(fake_text, max_iterations=2)

        assert res["verification_summary"]["final_status"] == "verified"
        assert res["verification_summary"]["corrected_and_verified_count"] >= 1
        assert "Deep Residual Learning for Image Recognition" in res["final_response"]


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
        assert "UNVERIFIED REFERENCE" in res["final_response"]


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
