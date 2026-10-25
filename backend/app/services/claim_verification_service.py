import re
from rapidfuzz import fuzz

STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are",
    "aren't", "as", "at", "be", "because", "been", "before", "being", "below", "between", "both",
    "but", "by", "can", "can't", "cannot", "could", "couldn't", "did", "didn't", "do", "does",
    "doesn't", "doing", "don't", "down", "during", "each", "few", "for", "from", "further", "had",
    "hadn't", "has", "hasn't", "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her",
    "here", "here's", "hers", "herself", "him", "himself", "his", "how", "how's", "i", "i'd",
    "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's", "its", "itself",
    "let's", "me", "more", "most", "mustn't", "my", "myself", "no", "nor", "not", "of", "off",
    "on", "once", "only", "or", "other", "ought", "our", "ours", "ourselves", "out", "over",
    "own", "same", "shan't", "she", "she'd", "she'll", "she's", "should", "shouldn't", "so",
    "some", "such", "than", "that", "that's", "the", "their", "theirs", "them", "themselves",
    "then", "there", "there's", "these", "they", "they'd", "they'll", "they're", "they've", "this",
    "those", "through", "to", "too", "under", "until", "up", "very", "was", "wasn't", "we", "we'd",
    "we'll", "we're", "we've", "were", "weren't", "what", "what's", "when", "when's", "where",
    "where's", "which", "while", "who", "who's", "whom", "why", "why's", "with", "won't", "would",
    "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your", "yours", "yourself", "yourselves",
    "paper", "papers", "author", "authors", "year", "venue", "doi", "published", "conference", "journal"
}


def _tokenize(text: str) -> set:
    if not text:
        return set()
    words = re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())
    return {w for w in words if w not in STOPWORDS}


def is_conversational_preamble(text: str) -> bool:
    """
    Check if a text passage is merely introductory conversational phrasing
    rather than an empirical or scientific claim about a paper.
    """
    t = text.strip().lower()
    if not t:
        return True
    if re.match(
        r"^(?:here\s+(?:is|are)|below\s+(?:is|are)|the\s+following\s+(?:is|are|reference|paper|citation)|please\s+find|as\s+requested|reference(?:s)?\s+(?:for|to|of)|citation(?:s)?\s+(?:for|to|of)|key\s+papers?|academic\s+reference|foundational\s+paper)\b",
        t,
    ):
        if len(t.split()) <= 15 or t.endswith(":"):
            return True
    return False


def extract_claim_for_citation(full_text: str, citation_text: str) -> str:
    """
    Extract the specific claim, summary, or contextual passage associated with a citation.
    """
    if not full_text or not citation_text:
        return ""

    # 1. Check for an explicit Summary/Context line inside the citation block
    summary_match = re.search(
        r"(?:^|\n)\s*(?:Summary|Context|Claim|Contribution|Description)\s*:\s*(.+)",
        citation_text,
        re.IGNORECASE
    )
    if summary_match:
        return summary_match.group(1).strip()

    # 2. Look in the preceding text of the response
    idx = full_text.find(citation_text)
    if idx > 0:
        preceding = full_text[:idx].strip()
        if preceding:
            paragraphs = [p.strip() for p in preceding.split("\n\n") if p.strip()]
            if paragraphs:
                last_p = paragraphs[-1]
                # Filter out headers like "References:" or section markers
                clean_lines = [
                    l.strip() for l in last_p.split("\n")
                    if not re.match(r"^(?:###\s*)?(?:References?|Bibliography|Sources?)\b", l.strip(), re.IGNORECASE)
                ]
                clean_text = " ".join(clean_lines).strip()
                if clean_text and not is_conversational_preamble(clean_text):
                    return clean_text

    # 3. Fallback to citation title
    title_match = re.search(r"Title\s*:\s*(.+)", citation_text, re.IGNORECASE)
    if title_match:
        return title_match.group(1).strip()

    first_line = citation_text.strip().split("\n")[0]
    clean_first = re.sub(r"^(?:\[\d+\]|\d+[\.\)]|Paper\s*\d+:?)\s*", "", first_line).strip()
    return clean_first


def verify_claim_support(claim_text: str, paper_record: dict) -> dict:
    """
    Assess whether the available evidence for the verified paper supports the associated claim.

    Outcomes:
    - supported: Reliable evidence (abstract/title) corroborates the claim concepts.
    - unsupported_claim: Retrieved evidence indicates the source addresses a different topic.
    - insufficient_evidence: Bibliographic existence verified, but full text or abstract is not
      available in public scholarly registries (Crossref, Semantic Scholar, OpenAlex).
    - not_found: Paper was not found in registries.
    """
    if not paper_record or paper_record.get("paper_exists") is False:
        return {
            "status": "not_found",
            "claim": claim_text,
            "supported": False,
            "confidence": 0.0,
            "evidence_type": "none",
            "evidence": None,
            "reason": "Referenced paper could not be found in scholarly registries; claim cannot be substantiated."
        }

    if paper_record.get("paper_exists") is None or paper_record.get("api_status") == "OUTAGE":
        return {
            "status": "insufficient_evidence",
            "claim": claim_text,
            "supported": None,
            "confidence": 0.0,
            "evidence_type": "none",
            "evidence": None,
            "reason": "Scholarly metadata registries were unreachable; claim support cannot be evaluated."
        }

    claim = (claim_text or "").strip()
    claim_tokens = _tokenize(claim)

    matched_title = paper_record.get("matched_title") or paper_record.get("title") or ""
    abstract = paper_record.get("matched_abstract") or paper_record.get("abstract")

    title_tokens = _tokenize(matched_title)

    # Case 1: Paper has abstract indexed
    if abstract and isinstance(abstract, str) and len(abstract.strip()) > 30:
        abstract_text = abstract.strip()
        abstract_tokens = _tokenize(abstract_text)
        corpus_tokens = title_tokens.union(abstract_tokens)

        overlap = claim_tokens.intersection(corpus_tokens)
        token_ratio = (len(overlap) / len(claim_tokens)) if claim_tokens else 0.5
        fuzz_score = fuzz.token_set_ratio(claim, f"{matched_title} {abstract_text}")

        # Clear semantic conflict / completely different subject
        if token_ratio < 0.15 or (token_ratio < 0.25 and fuzz_score < 45):
            return {
                "status": "unsupported_claim",
                "claim": claim,
                "supported": False,
                "confidence": 0.85,
                "evidence_type": "abstract",
                "evidence": abstract_text[:300] + ("..." if len(abstract_text) > 300 else ""),
                "reason": "The retrieved abstract indicates this paper addresses a different subject and does not substantiate the claim."
            }

        # Substantial topic congruence
        if token_ratio >= 0.25 or fuzz_score >= 40:
            return {
                "status": "supported",
                "claim": claim,
                "supported": True,
                "confidence": min(0.95, round(max(fuzz_score / 100.0, token_ratio), 2)),
                "evidence_type": "abstract",
                "evidence": abstract_text[:300] + ("..." if len(abstract_text) > 300 else ""),
                "reason": "Scholarly abstract corroborates the semantic concepts of the claim."
            }

        # Moderate topic presence
        return {
            "status": "supported",
            "claim": claim,
            "supported": True,
            "confidence": 0.70,
            "evidence_type": "abstract",
            "evidence": abstract_text[:300] + ("..." if len(abstract_text) > 300 else ""),
            "reason": "Abstract displays partial thematic alignment with the claim."
        }

    # Case 2: Full text and abstract are not indexed in public registries (metadata only)
    if claim_tokens:
        title_overlap = claim_tokens.intersection(title_tokens)
        title_overlap_ratio = len(title_overlap) / len(claim_tokens)
        title_fuzz = fuzz.token_set_ratio(claim, matched_title)

        if title_overlap_ratio < 0.08 and title_fuzz < 20:
            return {
                "status": "unsupported_claim",
                "claim": claim,
                "supported": False,
                "confidence": 0.75,
                "evidence_type": "metadata_only",
                "evidence": f"Verified Title: {matched_title}",
                "reason": "Paper title indicates a completely unrelated domain from the cited claim."
            }

    return {
        "status": "insufficient_evidence",
        "claim": claim,
        "supported": None,
        "confidence": 0.50,
        "evidence_type": "metadata_only",
        "evidence": f"Verified Title: {matched_title}",
        "reason": "Full text and abstract are not indexed in public registries (Crossref, Semantic Scholar, OpenAlex). Bibliographic metadata verified, but claim-to-source support requires full-text document access."
    }
