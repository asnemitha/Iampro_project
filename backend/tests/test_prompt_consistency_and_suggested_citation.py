import pytest
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "backend"))

from app.services.verification_pipeline import verify_response
from app.services.prompt_consistency_service import (
    extract_prompt_metadata,
    check_prompt_consistency,
)
from app.services.metadata_normalizer import canonicalize_verified_metadata
from app.services.citation_formatter import format_ieee


def test_a_bert_author_mismatch():
    """
    TEST A:
    Prompt requests BERT with incorrect authors (Geoffrey Hinton and Yann LeCun).
    LLM generates genuine BERT citation with true authors (Devlin et al.).

    Expected:
    - Bibliographic verification: paper_exists=True, citation_accurate=True, Valid Citation, score=0
    - Prompt consistency: matches=False, mismatched_fields contains 'authors'
    - Explanation highlights true authors vs prompt authors
    """
    user_prompt = (
        "Explain BERT and cite the paper 'BERT: Pre-training of Deep Bidirectional "
        "Transformers for Language Understanding' by Geoffrey Hinton and Yann LeCun, published in 2019."
    )

    llm_response = """1. BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding
Authors: Jacob Devlin, Ming-Wei Chang, Kenton Lee, Kristina Toutanova
Year: 2019
Venue: NAACL-HLT
DOI: 10.18653/v1/N19-1423"""

    results = verify_response(llm_response, user_prompt=user_prompt)

    assert len(results) == 1
    res = results[0]

    # Bibliographic verification must identify it as valid
    assert res["paper_exists"] is True
    assert res["citation_accurate"] is True
    assert res["hallucination_type"] == "Valid Citation"
    assert res["hallucination_score"] == 0

    # Prompt consistency must detect author mismatch
    pc = res["prompt_consistency"]
    assert pc is not None
    assert pc["checked"] is True
    assert pc["matches"] is False
    assert "authors" in pc["mismatched_fields"]
    assert "title" not in pc["mismatched_fields"]
    assert "year" not in pc["mismatched_fields"]

    # Check requested vs generated authors
    req_authors = " ".join(pc["requested_authors"])
    assert "Hinton" in req_authors
    assert "LeCun" in req_authors
    gen_authors = " ".join(pc["generated_authors"])
    assert "Devlin" in gen_authors

    # Check explanation
    assert "Devlin" in pc["explanation"] or "true authors" in pc["explanation"]
    assert "Hinton" in pc["explanation"] or "prompt" in pc["explanation"]


def test_b_field_by_field_prompt_consistency():
    """
    TEST B:
    Field-by-field prompt consistency checks:
    - Title, authors, year, venue, DOI.
    - Fields not in prompt should NOT be treated as mismatches.
    - prompt=None should return None.
    """
    # 1. Matching prompt
    prompt_match = (
        "Explain BERT and cite 'BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding' "
        "by Jacob Devlin, Ming-Wei Chang, Kenton Lee, Kristina Toutanova, published in 2019."
    )
    citation_data = {
        "title": "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding",
        "authors": ["Jacob Devlin", "Ming-Wei Chang", "Kenton Lee", "Kristina Toutanova"],
        "year": 2019,
        "venue": "NAACL",
        "doi": "10.18653/v1/N19-1423",
    }
    pc = check_prompt_consistency(prompt_match, citation_data)
    assert pc["checked"] is True
    assert pc["matches"] is True
    assert pc["mismatched_fields"] == []

    # 2. Wrong Year requested
    prompt_wrong_year = "Cite 'Attention Is All You Need' by Vaswani et al., published in 2024."
    citation_attn = {
        "title": "Attention Is All You Need",
        "authors": ["Ashish Vaswani", "Noam Shazeer"],
        "year": 2017,
        "venue": "NeurIPS",
        "doi": "10.48550/arXiv.1706.03762",
    }
    pc_year = check_prompt_consistency(prompt_wrong_year, citation_attn)
    assert pc_year["matches"] is False
    assert "year" in pc_year["mismatched_fields"]
    assert "authors" not in pc_year["mismatched_fields"]

    # 3. Wrong Title requested
    prompt_wrong_title = "Cite 'Deep Convolutional Networks for NLP' by Jacob Devlin, 2019."
    pc_title = check_prompt_consistency(prompt_wrong_title, citation_data)
    assert pc_title["matches"] is False
    assert "title" in pc_title["mismatched_fields"]

    # 4. Wrong Venue requested
    prompt_wrong_venue = "Cite 'Attention Is All You Need' by Vaswani, published in Nature, 2017."
    pc_venue = check_prompt_consistency(prompt_wrong_venue, citation_attn)
    assert pc_venue["matches"] is False
    assert "venue" in pc_venue["mismatched_fields"]

    # 5. Wrong DOI requested
    prompt_wrong_doi = "Cite 'Attention Is All You Need' with DOI 10.1000/wrong.doi"
    pc_doi = check_prompt_consistency(prompt_wrong_doi, citation_attn)
    assert pc_doi["matches"] is False
    assert "doi" in pc_doi["mismatched_fields"]

    # 6. Prompt without venue/DOI does NOT flag venue/DOI mismatch
    prompt_no_venue_doi = "Cite 'Attention Is All You Need' by Vaswani et al., published in 2017."
    pc_partial = check_prompt_consistency(prompt_no_venue_doi, citation_attn)
    assert pc_partial["matches"] is True
    assert "venue" not in pc_partial["mismatched_fields"]
    assert "doi" not in pc_partial["mismatched_fields"]

    # 7. user_prompt = None returns None
    assert check_prompt_consistency(None, citation_data) is None


def test_c_resnet_suggested_citation_canonicalization():
    """
    TEST C:
    ResNet citation with incorrect DOI.
    Suggested Citation must:
    - Have canonical publication year 2016 (not 2015 preprint year from OpenAlex)
    - Not contain duplicate years like '2016 IEEE Conference..., 2015'
    - Have canonical DOI '10.1109/CVPR.2016.90' (with uppercase CVPR)
    """
    user_prompt = (
        "Explain ResNet and cite the paper 'Deep Residual Learning for Image Recognition' "
        "by Kaiming He, Xiangyu Zhang, Shaoqing Ren, Jian Sun, published in 2016."
    )

    llm_response = """1. Deep Residual Learning for Image Recognition
Authors: Kaiming He, Xiangyu Zhang, Shaoqing Ren, Jian Sun
Year: 2016
Venue: IEEE Conference on Computer Vision and Pattern Recognition (CVPR)
DOI: 10.1109/WRONG.DOI.999"""

    results = verify_response(llm_response, user_prompt=user_prompt)

    assert len(results) == 1
    res = results[0]

    assert res["paper_exists"] is True
    assert res["citation_accurate"] is False  # Wrong DOI
    assert res["corrected_citation"] is not None

    corrected = res["corrected_citation"]
    print("Corrected citation:\n", corrected)

    # Must contain 2016
    assert "2016" in corrected
    # Must NOT contain 2015
    assert "2015" not in corrected
    # Must contain canonical DOI in uppercase CVPR
    assert "10.1109/CVPR.2016.90" in corrected
    # Must not contain duplicate conflicting years
    assert "2016, 2015" not in corrected
    assert "2016 IEEE Conference on Computer Vision and Pattern Recognition (CVPR), 2015" not in corrected

    # Verified matched metadata should also reflect canonical year
    assert res["matched_year"] == 2016
    assert "CVPR.2016.90" in res["matched_doi"]


def test_d_regression_check_valid_citations():
    """
    TEST D:
    Transformer, BERT, and ResNet remain Valid Citations with hallucination score 0
    when citations are correct.
    """
    # 1. Attention Is All You Need
    attn_resp = """1. Attention Is All You Need
Authors: Ashish Vaswani, Noam Shazeer, Niki Parmar, Jakob Uszkoreit, Llion Jones, Aidan N. Gomez, Łukasz Kaiser, Illia Polosukhin
Year: 2017
Venue: Advances in Neural Information Processing Systems (NeurIPS)
DOI: 10.48550/arXiv.1706.03762"""

    attn_res = verify_response(attn_resp)
    assert len(attn_res) == 1
    assert attn_res[0]["paper_exists"] is True
    assert attn_res[0]["citation_accurate"] is True
    assert attn_res[0]["hallucination_score"] == 0
    assert attn_res[0]["hallucination_type"] == "Valid Citation"
    # Backward compatibility: prompt_consistency is None when user_prompt is not passed
    assert attn_res[0]["prompt_consistency"] is None

    # 2. ResNet with accurate metadata
    resnet_resp = """1. Deep Residual Learning for Image Recognition
Authors: Kaiming He, Xiangyu Zhang, Shaoqing Ren, Jian Sun
Year: 2016
Venue: IEEE Conference on Computer Vision and Pattern Recognition (CVPR)
DOI: 10.1109/CVPR.2016.90"""

    resnet_res = verify_response(resnet_resp)
    assert len(resnet_res) == 1
    assert resnet_res[0]["paper_exists"] is True
    assert resnet_res[0]["citation_accurate"] is True
    assert resnet_res[0]["hallucination_score"] == 0
    assert resnet_res[0]["hallucination_type"] == "Valid Citation"


def test_e_gan_wrong_doi_prefers_original():
    """
    TEST E:
    GAN citation with incorrect DOI.
    Prompt explicitly requests:
    "Explain GANs and cite the original paper 'Generative Adversarial Nets' by Ian J. Goodfellow et al., published in 2014."
    LLM generates citation with wrong DOI.

    Expected:
    - paper_exists is True
    - citation_accurate is False (due to wrong DOI)
    - Suggested Citation selects the original 2014 NeurIPS paper rather than 2020 CACM reprint/survey
    - Title: "Generative Adversarial Nets"
    - Authors: contains Goodfellow et al.
    - Publication Year: 2014 (NOT 2020)
    - Venue: Neural Information Processing Systems (NeurIPS) (NOT Communications of the ACM)
    - DOI: 10.48550/arXiv.1406.2661
    """
    user_prompt = (
        'Explain GANs and cite the original paper "Generative Adversarial Nets" '
        'by Ian J. Goodfellow et al., published in 2014.'
    )

    llm_response = """1. Generative Adversarial Nets
Authors: Ian J. Goodfellow, Jean Pouget-Abadie, Mehdi Mirza, Bing Xu, David Warde-Farley, Sherjil Ozair, Aaron Courville, Yoshua Bengio
Year: 2014
Venue: Neural Information Processing Systems
DOI: 10.1145/WRONG.DOI"""

    results = verify_response(llm_response, user_prompt=user_prompt)

    assert len(results) == 1
    res = results[0]

    assert res["paper_exists"] is True
    assert res["citation_accurate"] is False  # Wrong DOI
    assert res["corrected_citation"] is not None

    corrected = res["corrected_citation"]
    print("Corrected GAN citation:\n", corrected)

    # Must be the 2014 original publication
    assert "2014" in corrected
    assert "2020" not in corrected

    # Must be Neural Information Processing Systems (NeurIPS), NOT Communications of the ACM
    assert "Communications of the ACM" not in corrected
    assert "Neural Information Processing Systems" in corrected

    # Must contain original title
    assert "Generative Adversarial Nets" in corrected

    # Must contain Goodfellow
    assert "Goodfellow" in corrected

    # Must have canonical DOI
    assert "10.48550/arXiv.1406.2661" in corrected

    # Check matched metadata fields
    assert res["matched_year"] == 2014
    assert "Neural Information Processing Systems" in res["matched_venue"]
    assert "1406.2661" in res["matched_doi"]


def test_f_photosynthesis_citation_1_doi_first():
    """
    SCENARIO 7:
    Real DOI with hallucinated metadata:
    "Molecular mechanisms of photosynthetic light harvesting"
    Authors: Fleming, G. R., Scholes, G. D., & Cheng, Y. C.
    Year: 2004
    Venue: Procedia Chemistry
    DOI: 10.1016/j.proche.2009.12.018

    Expected:
    - Real DOI resolves to Zoltan Pataj et al., Procedia Chemistry, 2010.
    - DOI-first verification retains verified paper from authoritative DOI lookup.
    - paper_exists = True
    - citation_accurate = False
    - hallucination_type = "Metadata Hallucination"
    - Suggested Citation suggests the genuine paper (Zoltan Pataj et al.).
    """
    llm_citation = '''1. "Molecular mechanisms of photosynthetic light harvesting"
Authors: Fleming, G. R., Scholes, G. D., & Cheng, Y. C.
Year: 2004
Venue: Procedia Chemistry
DOI: 10.1016/j.proche.2009.12.018'''

    results = verify_response(llm_citation)
    assert len(results) == 1
    res = results[0]

    # DOI belongs to an unrelated publication (Zoltan Pataj et al., beta-lactams); not adopted as candidate for photosynthesis citation
    assert res["paper_exists"] is False
    assert res["citation_accurate"] is False
    assert res["hallucination_type"] == "Fabricated Citation"
    assert res["doi_match"] is False


def test_g_photosynthesis_citation_2_fake_doi():
    """
    SCENARIO 8:
    Fake DOI + fabricated title:
    "Structure and function of Photosystem II"
    Authors: Barber, J.
    Year: 2003
    Venue: Biochimica et Biophysica Acta (BBA) - Bioenergetics
    DOI: 10.1016/S0005-2728(03)00029-0

    Expected:
    - DOI 404 fails
    - Candidate search does not match noisy book chapters with low title overlap
    - paper_exists = False
    - citation_accurate = False
    - hallucination_type = "Fabricated Citation"
    - hallucination_score = 100
    - corrected_citation = None
    """
    llm_citation = '''2. "Structure and function of Photosystem II"
Authors: Barber, J.
Year: 2003
Venue: Biochimica et Biophysica Acta (BBA) - Bioenergetics
DOI: 10.1016/S0005-2728(03)00029-0'''

    results = verify_response(llm_citation)
    assert len(results) == 1
    res = results[0]

    assert res["paper_exists"] is False
    assert res["citation_accurate"] is False
    assert res["hallucination_type"] == "Fabricated Citation"
    assert res["hallucination_score"] == 100
    assert res["corrected_citation"] is None


def test_h_photosynthesis_citation_3_fake_doi():
    """
    SCENARIO 9:
    Fake DOI + fabricated title:
    "The Calvin cycle and its regulation"
    Authors: Bassham, J. A.
    Year: 2003
    Venue: Photosynthesis Research
    DOI: 10.1023/A:1025785025251

    Expected:
    - DOI 404 fails
    - Bassham never wrote a paper with this title
    - paper_exists = False
    - citation_accurate = False
    - hallucination_type = "Fabricated Citation"
    - hallucination_score = 100
    - corrected_citation = None
    """
    llm_citation = '''3. "The Calvin cycle and its regulation"
Authors: Bassham, J. A.
Year: 2003
Venue: Photosynthesis Research
DOI: 10.1023/A:1025785025251'''

    results = verify_response(llm_citation)
    assert len(results) == 1
    res = results[0]

    assert res["paper_exists"] is False
    assert res["citation_accurate"] is False
    assert res["hallucination_type"] == "Fabricated Citation"
    assert res["hallucination_score"] == 100
    assert res["corrected_citation"] is None


def test_i_bert_valid_citation():
    """
    SCENARIO 1:
    Valid Devlin BERT citation with accurate metadata.
    """
    bert_citation = '''1. BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding
Authors: Jacob Devlin, Ming-Wei Chang, Kenton Lee, Kristina Toutanova
Year: 2019
Venue: NAACL-HLT
DOI: 10.18653/v1/N19-1423'''

    results = verify_response(bert_citation)
    assert len(results) == 1
    res = results[0]

    assert res["paper_exists"] is True
    assert res["citation_accurate"] is True
    assert res["hallucination_score"] == 0
    assert res["hallucination_type"] == "Valid Citation"


def test_j_photosynthesis_citation_1_scholes_doi_corroboration():
    """
    Safe Prompt Photosynthesis Citation 1:
    Prompt: "Explain how photosynthesis works in plants and describe the role of chlorophyll."
    Citation:
    Title: Light harvesting in photosynthesis
    Authors: Gregory D. Scholes, Graham R. Fleming, Alexandra Olaya-Castro, Rienk van Grondelle
    Year: 2011
    Venue: Nature Chemistry
    DOI: 10.1038/nchem.1145

    Expected:
    - Authoritative DOI 10.1038/nchem.1145 resolves to "Lessons from nature about solar light harvesting"
    - Authors match (100%), Year matches (100%), Venue matches (100%), DOI matches (100%)
    - DOI paper is retained over authorless book distractors ("Light Harvesting in Photosynthesis", 2018, CRC Press)
    - paper_exists = True
    - citation_accurate = False (Title differs)
    - hallucination_type = "Metadata Hallucination"
    - corrected_citation contains Scholes et al., "Lessons from nature about solar light harvesting", 2011, DOI: 10.1038/nchem.1145
    - corrected_citation does NOT contain "Unknown Author" or CRC Press book
    """
    citation = '''Citation 1:
Title: Light harvesting in photosynthesis
Authors: Gregory D. Scholes, Graham R. Fleming, Alexandra Olaya-Castro, Rienk van Grondelle
Year: 2011
Venue: Nature Chemistry
DOI: 10.1038/nchem.1145'''

    results = verify_response(citation)
    assert len(results) == 1
    res = results[0]

    assert res["paper_exists"] is True
    assert res["citation_accurate"] is False
    assert res["hallucination_type"] == "Metadata Hallucination"
    assert res["matched_title"] == "Lessons from nature about solar light harvesting"
    assert res["corrected_citation"] is not None
    assert "Scholes" in res["corrected_citation"]
    assert "Lessons from nature about solar light harvesting" in res["corrected_citation"]
    assert "10.1038/nchem.1145" in res["corrected_citation"]
    assert "Unknown Author" not in res["corrected_citation"]
    assert "10.1201/9781351242899" not in res["corrected_citation"]


def test_k_photosynthesis_citation_2_shen_fake_doi_canonical_correction():
    """
    Safe Prompt Photosynthesis Citation 2:
    Prompt: "Explain how photosynthesis works in plants and describe the role of chlorophyll."
    Citation:
    Title: The Structure of Photosystem II and the Mechanism of Water Oxidation
    Authors: Jian-Ren Shen
    Year: 2015
    Venue: Annual Review of Plant Biology
    DOI: 10.1146/annurev-arplant-043014-114600

    Expected:
    - Supplied DOI is fake / does not resolve
    - Multi-source retrieval identifies canonical paper: "The Structure of Photosystem II and the Mechanism of Water Oxidation in Photosynthesis"
    - Canonical DOI: 10.1146/annurev-arplant-050312-120129
    - paper_exists = True
    - citation_accurate = False (DOI differs)
    - hallucination_type = "Metadata Hallucination"
    - corrected_citation contains Jian-Ren Shen and canonical DOI 10.1146/annurev-arplant-050312-120129
    """
    citation = '''Citation 2:
Title: The Structure of Photosystem II and the Mechanism of Water Oxidation
Authors: Jian-Ren Shen
Year: 2015
Venue: Annual Review of Plant Biology
DOI: 10.1146/annurev-arplant-043014-114600'''

    results = verify_response(citation)
    assert len(results) == 1
    res = results[0]

    assert res["paper_exists"] is True
    assert res["citation_accurate"] is False
    assert res["hallucination_type"] == "Metadata Hallucination"
    assert res["corrected_citation"] is not None
    assert "Shen" in res["corrected_citation"]
    assert "10.1146/annurev-arplant-050312-120129" in res["corrected_citation"]


def test_l_sql_injection_doi_first_canonical_record():
    """
    SQL Injection Citation 1:
    Supplied:
    Title: A Classification of SQL Injection Attacks and Countermeasures
    Authors: William G. J. Halfond, Jeremy Viegas, Alessandro Orso
    Year: 2006
    Venue: ISSTA
    DOI: 10.1145/1146238.1146241

    Investigation:
    DOI 10.1145/1146238.1146241 is canonically registered in Crossref/ACM to:
    Phil McMinn, Mark Harman, David Binkley, Paolo Tonella,
    "The species per path approach to SearchBased test data generation", ISSTA 2006.

    Expected:
    - paper_exists = True (real DOI)
    - citation_accurate = False (Title & authors differ from the record owning this DOI)
    - hallucination_type = "Metadata Hallucination"
    - corrected_citation suggests the canonical paper associated with this DOI: McMinn et al., "The species per path approach..."
    """
    citation = '''Title: A Classification of SQL Injection Attacks and Countermeasures
Authors: William G. J. Halfond, Jeremy Viegas, Alessandro Orso
Year: 2006
Venue: ISSTA
DOI: 10.1145/1146238.1146241'''

    results = verify_response(citation)
    assert len(results) == 1
    res = results[0]

    assert res["paper_exists"] is True
    assert res["citation_accurate"] is False
    assert res["hallucination_type"] == "Metadata Hallucination"
    assert "Halfond" in res["corrected_citation"]
    assert "A Classification of SQL" in res["corrected_citation"]



