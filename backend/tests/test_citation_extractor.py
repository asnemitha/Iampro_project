import pytest
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "backend"))

from app.services.citation_extractor import extract_citations, is_valid_citation
from app.services.verification_pipeline import verify_response


def test_a_explanatory_numbered_list():
    """
    TEST A — explanatory numbered list:
    1. Self-Attention Mechanism
    2. Multi-Head Attention
    3. Encoder-Decoder Structure

    Expected: No citations extracted.
    """
    text = """1. Self-Attention Mechanism
2. Multi-Head Attention
3. Encoder-Decoder Structure"""

    citations = extract_citations(text)
    assert len(citations) == 0, f"Expected 0 citations, got: {citations}"


def test_b_genuine_numbered_citation():
    """
    TEST B — genuine numbered citation:
    1. Attention Is All You Need
    Authors: Ashish Vaswani, Noam Shazeer, Niki Parmar, Jakob Uszkoreit, Llion Jones, Aidan N. Gomez, Aidan N. Gomez, Łukasz Kaiser, Illia Polosukhin
    Year: 2017
    Venue: NeurIPS
    DOI: 10.48550/arXiv.1706.03762

    Expected: Exactly one citation extracted.
    """
    text = """1. Attention Is All You Need
Authors: Ashish Vaswani, Noam Shazeer, Niki Parmar, Jakob Uszkoreit, Llion Jones, Aidan N. Gomez, Aidan N. Gomez, Łukasz Kaiser, Illia Polosukhin
Year: 2017
Venue: NeurIPS
DOI: 10.48550/arXiv.1706.03762"""

    citations = extract_citations(text)
    assert len(citations) == 1, f"Expected 1 citation, got: {len(citations)}"
    assert "Attention Is All You Need" in citations[0]
    assert "10.48550/arXiv.1706.03762" in citations[0]


def test_c_explanation_followed_by_citation():
    """
    TEST C — ordinary numbered explanation followed by citation:
    1. Self-Attention Mechanism
    2. Multi-Head Attention
    3. Encoder-Decoder Structure

    1. Attention Is All You Need
    Authors: Ashish Vaswani et al.
    Year: 2017
    Venue: NeurIPS
    DOI: 10.48550/arXiv.1706.03762

    Expected: Only the bibliographic citation is extracted.
    """
    text = """1. Self-Attention Mechanism
2. Multi-Head Attention
3. Encoder-Decoder Structure

1. Attention Is All You Need
Authors: Ashish Vaswani et al.
Year: 2017
Venue: NeurIPS
DOI: 10.48550/arXiv.1706.03762"""

    citations = extract_citations(text)
    assert len(citations) == 1, f"Expected 1 citation, got {len(citations)}: {citations}"
    assert "Attention Is All You Need" in citations[0]
    assert "Self-Attention Mechanism" not in citations[0]
    assert "Multi-Head Attention" not in citations[0]


def test_d_bracketed_ieee_citation():
    """
    TEST D — [1] citation:
    [1] Attention Is All You Need — Vaswani et al., 2017.

    Expected: One citation extracted.
    """
    text = """[1] Attention Is All You Need — Vaswani et al., 2017."""

    citations = extract_citations(text)
    assert len(citations) == 1, f"Expected 1 citation, got: {len(citations)}"
    assert "Attention Is All You Need" in citations[0]


def test_e_paper_format():
    """
    TEST E — Paper format:
    Paper 1: Attention Is All You Need
    Authors: Ashish Vaswani et al.
    Year: 2017
    DOI: 10.48550/arXiv.1706.03762

    Expected: One citation extracted.
    """
    text = """Paper 1: Attention Is All You Need
Authors: Ashish Vaswani et al.
Year: 2017
DOI: 10.48550/arXiv.1706.03762"""

    citations = extract_citations(text)
    assert len(citations) == 1, f"Expected 1 citation, got: {len(citations)}"
    assert "Attention Is All You Need" in citations[0]


def test_numbered_points_and_sentences():
    """
    Ordinary numbered sentences or points must not be extracted.
    """
    text = """1. First point about machine learning
2. Second point about neural networks
3. Third point about gradient descent optimization"""

    citations = extract_citations(text)
    assert len(citations) == 0, f"Expected 0 citations, got: {citations}"


def test_raw_benchmark_metadata_block():
    """
    Ensure benchmark format beginning with 'Title:' is correctly extracted.
    """
    text = """Title: "A Machine Learning Approach to POS Tagging"
Authors: Lluís Màrquez; Lluís Padró; Horacio Rodríguez
Year: 2005
Venue: Machine Learning
DOI: 10.1023/a:1007673816718"""

    citations = extract_citations(text)
    assert len(citations) == 1, f"Expected 1 citation, got: {len(citations)}"
    assert "A Machine Learning Approach to POS Tagging" in citations[0]


def test_general_papers_not_hardcoded():
    """
    Ensure extraction works generally for other academic papers (BERT, ResNet, AlexNet, GANs, Adam, U-Net).
    """
    papers = [
        """1. BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding
Authors: Jacob Devlin, Ming-Wei Chang, Kenton Lee, Kristina Toutanova
Year: 2018
arXiv: 1810.04805""",

        """1. Deep Residual Learning for Image Recognition
Authors: Kaiming He, Xiangyu Zhang, Shaoqing Ren, Jian Sun
Year: 2016
Venue: CVPR
DOI: 10.1109/CVPR.2016.90""",

        """1. ImageNet Classification with Deep Convolutional Neural Networks
Authors: Alex Krizhevsky, Ilya Sutskever, Geoffrey E. Hinton
Year: 2012
Venue: NeurIPS""",

        """1. Generative Adversarial Networks
Authors: Ian J. Goodfellow et al.
Year: 2014
Venue: NeurIPS""",

        """1. Adam: A Method for Stochastic Optimization
Authors: Diederik P. Kingma, Jimmy Ba
Year: 2014
Conference: ICLR
arXiv: 1412.6980""",

        """1. U-Net: Convolutional Networks for Biomedical Image Segmentation
Authors: Olaf Ronneberger, Philipp Fischer, Thomas Brox
Year: 2015
Venue: MICCAI
DOI: 10.1007/978-3-319-24574-4_28"""
    ]

    for p in papers:
        c = extract_citations(p)
        assert len(c) == 1, f"Failed to extract citation for:\n{p}"


def test_transformer_response_end_to_end():
    """
    Exact Transformer response that caused the false-positive bug during testing.
    Verifies that:
    - Numbered explanation sections (1 to 5) are NOT extracted.
    - Only the genuine Attention Is All You Need citation is extracted.
    - End-to-end verification pipeline verifies it as a Valid Citation with 0 hallucination score.
    """
    response = """Explain the Transformer architecture and cite the original paper "Attention Is All You Need" by Vaswani et al., published in 2017.

The Transformer model introduces several key components:

1. Self-Attention Mechanism
It computes representation by comparing tokens' positions in the sequence.

2. Multi-Head Attention
Allows the model to jointly attend to information from different representation subspaces.

3. Encoder-Decoder Structure
The encoder processes the input sequence, and the decoder generates output tokens.

4. Positional Encoding
Adds information about the token's position in the sequence, since attention is permutation-invariant.

5. Residual Connections and Layer Normalization
Employed around each of the sub-layers in 2017.

References:
1. Attention Is All You Need
Authors: Ashish Vaswani, Noam Shazeer, Niki Parmar, Jakob Uszkoreit, Llion Jones, Aidan N. Gomez, Łukasz Kaiser, Illia Polosukhin
Year: 2017
Venue: Advances in Neural Information Processing Systems (NeurIPS)
DOI: 10.48550/arXiv.1706.03762"""

    citations = extract_citations(response)
    assert len(citations) == 1, f"Expected exactly 1 citation, got {len(citations)}: {citations}"
    assert "Attention Is All You Need" in citations[0]

    # Verify no explanation headings were extracted
    for heading in [
        "Self-Attention Mechanism",
        "Multi-Head Attention",
        "Encoder-Decoder Structure",
        "Positional Encoding",
        "Residual Connections and Layer Normalization",
    ]:
        assert not any(heading in c and "Attention Is All You Need" not in c for c in citations), \
            f"Explanation heading '{heading}' was erroneously extracted as a citation!"

    # Run end-to-end verification pipeline
    results = verify_response(response)
    assert len(results) == 1, f"Expected 1 verification result, got {len(results)}"
    res = results[0]
    assert res["paper_exists"] is True
    assert res["citation_accurate"] is True
    assert res["hallucination_type"] == "Valid Citation"
    assert res["hallucination_score"] == 0
