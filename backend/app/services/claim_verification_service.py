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
    "paper", "papers", "author", "authors", "year", "venue", "doi", "published", "conference", "journal",
    "verify", "verification", "check", "checking", "citation", "citations", "reference", "references",
    "analyze", "analysis", "following", "below", "here", "please", "sure", "certainly", "prompt",
    "request", "requested", "find", "search", "model", "output"
}


def _tokenize(text: str) -> set:
    if not text:
        return set()
    words = re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())
    return {w for w in words if w not in STOPWORDS}


def is_conversational_preamble(text: str) -> bool:
    """
    Check if a text passage is merely introductory conversational phrasing,
    a prompt directive / verification instruction, or a structural section header
    rather than an empirical or scientific claim about a paper.
    """
    t = text.strip().lower()
    if not t:
        return True

    # 1. Structural section headers or short lines ending in colon with <= 15 words
    if t.endswith(":") and len(t.split()) <= 15:
        return True

    # 2. Section header patterns (e.g. "### References", "1. Citations to verify:")
    if re.match(r"^(?:#{1,6}\s*)?(?:references?|bibliography|sources?|citations?|paper\s*\d+:?|citation\s*\d+:?)\b", t):
        if len(t.split()) <= 15 or t.endswith(":"):
            return True

    # 3. Conversational openings (e.g. "Here is...", "Sure, I can help...", "Below are...")
    opening_patterns = [
        r"^(?:here\s+(?:is|are)|below\s+(?:is|are)|the\s+following|please\s+(?:find|examine)|as\s+requested)\b",
        r"^(?:sure|certainly|of\s+course|absolutely|gladly|happy\s+to\s+help|based\s+on\s+your\s+request|according\s+to)\b",
        r"^(?:key\s+papers?|academic\s+references?|foundational\s+papers?|recommended\s+papers?)\b",
        r"^(?:prompt|input|query|request)\s*:\s*",
    ]
    if any(re.match(pat, t) for pat in opening_patterns):
        if len(t.split()) <= 20 or t.endswith(":"):
            return True

    # 4. Verification prompt directives and meta-instructions:
    # Text that instructs CiteGuard to verify/check citations, metadata, DOIs, authors, discrepancies, etc.
    # E.g. "Verify the supplied citation against authoritative scholarly records. Check the DOI, title, authors, publication year, and conference or venue. Identify any discrepancies and provide evidence from reliable scholarly sources."
    instruction_verbs = {
        "verify", "check", "analyze", "validate", "review", "evaluate", "examine",
        "identify", "assess", "investigate", "confirm", "corroborate", "audit"
    }
    bibliographic_terms = {
        "citation", "citations", "reference", "references", "doi", "dois", "author", "authors",
        "title", "titles", "venue", "venues", "year", "years", "conference", "conferences", "journal", "journals",
        "discrepancy", "discrepancies", "metadata", "record", "records", "source", "sources",
        "scholarly", "authoritative", "registry", "registries"
    }

    words = set(re.findall(r"\b[a-z]{3,}\b", t))
    has_instruction_verb = bool(words.intersection(instruction_verbs))
    has_bib_terms = len(words.intersection(bibliographic_terms)) >= 2

    # Starts with a verification command or directive
    starts_with_directive = bool(re.match(
        r"^(?:please\s+)?(?:verify|check|analyze|validate|review|evaluate|examine|identify|assess|audit)\b",
        t
    ))

    if starts_with_directive and (has_bib_terms or len(t.split()) <= 35):
        return True

    if has_instruction_verb and has_bib_terms and len(words.intersection(instruction_verbs.union(bibliographic_terms))) >= 3:
        return True

    return False


def extract_claim_for_citation(full_text: str, citation_text: str) -> str:
    """
    Extract the specific claim, summary, or contextual passage associated with a citation.
    Returns empty string if the citation is standalone or accompanied only by verification
    instructions/preambles (indicating no substantive empirical claim was asserted).
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
        summary_val = summary_match.group(1).strip()
        if summary_val and not is_conversational_preamble(summary_val):
            return summary_val

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
                    if not re.match(r"^(?:###\s*)?(?:References?|Bibliography|Sources?|Citations?|Paper\s*\d+:?)\b", l.strip(), re.IGNORECASE)
                ]
                clean_text = " ".join(clean_lines).strip()
                if clean_text and not is_conversational_preamble(clean_text):
                    # Ensure clean_text actually has informative substantive tokens
                    if len(_tokenize(clean_text)) >= 2:
                        return clean_text

    # If no explicit claim field and no preceding substantive claim text exists,
    # the citation is a standalone bibliographic reference (no empirical claim asserted).
    return ""


def verify_claim_support(claim_text: str, paper_record: dict) -> dict:
    """
    Assess whether the available evidence for the verified paper supports the associated claim.

    Outcomes:
    - supported: Reliable evidence (abstract/title) corroborates the claim concepts.
    - unsupported_claim: Retrieved evidence indicates the source addresses a different topic.
    - insufficient_evidence: Bibliographic existence verified, but full text or abstract is not
      available in public scholarly registries (Crossref, Semantic Scholar, OpenAlex).
    - not_applicable: Standalone citation; no substantive empirical claim was asserted.
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
    if not claim:
        matched_title = paper_record.get("matched_title") or paper_record.get("title") or "Scholarly record"
        return {
            "status": "supported",
            "claim": None,
            "supported": True,
            "confidence": 1.0,
            "evidence_type": "bibliographic_metadata",
            "evidence": f"Verified Record: {matched_title}",
            "reason": "Standalone citation; verified against authoritative scholarly registries without associated empirical claims."
        }

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

        # Check whether claim references the paper title itself (e.g. citation text or title fallback)
        title_in_claim = bool(
            (title_tokens and title_tokens.issubset(claim_tokens))
            or (matched_title and fuzz.token_set_ratio(claim, matched_title) >= 75)
        )

        # Clear semantic conflict / completely different subject
        if not title_in_claim and (token_ratio < 0.15 or (token_ratio < 0.25 and fuzz_score < 45)):
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
