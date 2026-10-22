import re


def is_valid_citation(block: str) -> bool:
    """
    Check if a candidate text block is a genuine academic citation
    rather than an explanatory section, heading, or ordinary numbered list.
    """
    block = block.strip()
    if not block or len(block) < 6:
        return False

    lines = [l.strip() for l in block.split("\n") if l.strip()]
    if not lines:
        return False

    first_line = lines[0]
    block_lower = block.lower()

    # 1. IEEE bracketed citations: [1], [2], etc.
    if re.match(r"^\[\d+\]", first_line):
        return len(block) > 10

    # 2. Paper prefix: 'Paper 1:', '### Paper 1', '**Paper 1**'
    if re.match(r"^(?:###\s*)?(?:\*\*)?Paper\s*\d+", first_line, re.IGNORECASE):
        return True

    # 3. Raw metadata block starting with Title: (Benchmark format)
    if re.match(r"^(?:###\s*)?(?:\*\*)?Title\s*:", first_line, re.IGNORECASE):
        return True

    # Explicit metadata fields across the block
    has_authors_field = bool(re.search(r"(?:^|\n)\s*(?:\d+[\.\)]\s*)?\**\s*Authors?\s*:", block, re.IGNORECASE))
    has_venue_field = bool(re.search(r"(?:^|\n)\s*(?:\d+[\.\)]\s*)?\**\s*(?:Venue|Conference|Journal|Booktitle|Published\s+in)\s*:", block, re.IGNORECASE))
    has_year_field = bool(re.search(r"(?:^|\n)\s*(?:\d+[\.\)]\s*)?\**\s*Year\s*:\s*(19|20)\d{2}\b", block, re.IGNORECASE))
    has_doi_field = bool(re.search(r"(?:^|\n)\s*(?:\d+[\.\)]\s*)?\**\s*DOI\s*:", block, re.IGNORECASE))
    has_arxiv_field = bool(re.search(r"(?:^|\n)\s*(?:\d+[\.\)]\s*)?\**\s*arXiv\s*:", block, re.IGNORECASE))
    has_title_field = bool(re.search(r"(?:^|\n)\s*(?:\d+[\.\)]\s*)?\**\s*Title\s*:", block, re.IGNORECASE))

    has_doi = bool(re.search(r"\b10\.\d{4,9}/[-._;()/:A-Za-z0-9]+", block, re.IGNORECASE))
    has_arxiv = bool(re.search(r"\barXiv:\s*\d{4}\.\d{4,5}\b", block, re.IGNORECASE))

    # Academic field presence: If explicit scholarly fields exist, it's a metadata block
    if has_doi_field or has_arxiv_field or has_doi or has_arxiv:
        return True
    if has_authors_field:
        return True
    if has_venue_field and (has_year_field or re.search(r"\b(19|20)\d{2}\b", block)):
        return True
    if has_title_field and (has_year_field or has_authors_field or has_venue_field or has_doi_field):
        return True

    # Check for inline bibliographic citations (e.g. "1. Attention Is All You Need — Vaswani et al., 2017.")
    has_et_al = bool(re.search(r"\bet\s+al\.?\b", block, re.IGNORECASE))
    has_by_author = bool(re.search(r"\bby\s+[A-Z][a-zA-Z\s,]+", block))
    has_year = bool(re.search(r"\b(19|20)\d{2}\b", block))
    has_citation_year = bool(re.search(r"(?:\((19|20)\d{2}\)|[,\—\-]\s*(19|20)\d{2}\b)", block))

    venue_keywords = [
        "ieee", "acm", "springer", "neurips", "nips", "cvpr", "iccv",
        "eccv", "icml", "iclr", "nature", "science", "naacl", "acl",
        "emnlp", "pnas", "proceedings", "transactions", "journal",
        "neural information processing systems"
    ]
    has_venue_keyword = any(v in block_lower for v in venue_keywords)
    has_vol_pp = bool(re.search(r"\b(?:vol\.|pp\.|no\.|pages)\s*\d+", block, re.IGNORECASE))
    has_quoted_title = bool(re.search(r'["“][^"”\n]{5,}["”]', block))
    has_dash_separator = bool(re.search(r"\s+[—\-]\s+[A-Z]", block))
    has_apa_authors = bool(re.search(r"\b[A-Z][a-z]+,\s*[A-Z]\.", block))
    has_parenthesized_year = bool(re.search(r"\((19|20)\d{2}\)", block))

    # APA style: Author, A. ... (Year). Title
    if has_apa_authors and has_parenthesized_year:
        return True

    # Author attribution + year + bibliographic anchor
    if (has_et_al or has_by_author) and has_year:
        if has_dash_separator or has_quoted_title or has_venue_keyword or has_vol_pp or has_citation_year:
            if len(lines) > 1 and not (has_dash_separator or has_quoted_title):
                clean_first = re.sub(r"^\d+[\.\)]\s*", "", first_line).strip()
                if not any(c in clean_first for c in [",", ";", "(", "—", "-", '"', "“"]):
                    return False
            return True

    # Inline citation with venue + year + volume/pages
    if has_venue_keyword and has_year and (has_vol_pp or has_quoted_title):
        return True

    return False


def extract_citations(text: str):
    """
    Extract citations from LLM responses.

    Supports:
    1. IEEE references ([1] ...)
    2. Numbered academic citations (1. Title \n Authors: ... or 1. Title - Author, Year)
    3. Paper-prefixed citations (Paper 1: ... or ### Paper 1)
    4. Raw metadata blocks (Title: ... \n Authors: ...)
    5. Inline citations (APA, arXiv, DOI)

    Robustly distinguishes between numbered explanation/list items
    and genuine bibliographic citations.
    """
    if not text:
        return []

    text = text.replace("\r\n", "\n")
    lines = text.split("\n")
    citations = []
    current = []

    paper_pattern = re.compile(r"^(?:###\s*)?(?:\*\*)?(?:Paper|Citation)\s*\d+", re.IGNORECASE)
    ieee_pattern = re.compile(r"^\[\d+\]")
    numbered_subfield = re.compile(
        r"^\d+\.\s*\**\s*(?:Authors?|Venue|Conference|Journal|Year|DOI|arXiv|Abstract|Summary|Key Contribution|Link|Publication)\b",
        re.IGNORECASE,
    )
    # Do not treat 4-digit years (e.g. 2022.) as list item numbers
    numbered_pattern = re.compile(r"^(?!(?:19|20)\d{2}\.)\d+[\.\)]\s*", re.IGNORECASE)
    title_start_pattern = re.compile(r"^(?:###\s*)?(?:\*\*)?Title\s*:", re.IGNORECASE)
    references_header_pattern = re.compile(
        r"^(?:###\s*)?(?:\*\*)?(?:References?|Bibliography|Works Cited|Citations?|Sources?)(?:\*\*)?\s*:?$",
        re.IGNORECASE,
    )
    divider_pattern = re.compile(r"^---+")

    def flush_current():
        nonlocal current
        if current:
            block = "\n".join(current).strip()
            if block:
                citations.append(block)
            current = []

    for line in lines:
        stripped = line.strip()

        if not stripped:
            continue

        # Section headers (e.g. "References:") or dividers flush any preceding block
        # and are not included in citation blocks
        if references_header_pattern.match(stripped) or divider_pattern.match(stripped):
            flush_current()
            continue

        # Check if line indicates start of a new citation
        is_new_citation = False

        if paper_pattern.match(stripped) or ieee_pattern.match(stripped):
            is_new_citation = True
        elif title_start_pattern.match(stripped):
            # If current citation already contains a title, this starts a new citation
            if current and any(re.search(r"Title\s*:", c, re.IGNORECASE) for c in current):
                is_new_citation = True
            elif not current:
                is_new_citation = True
        elif numbered_pattern.match(stripped):
            is_subfield = False
            if current:
                if numbered_subfield.match(stripped):
                    is_subfield = True
                elif any(paper_pattern.match(c) for c in current) and re.match(r"^\d+\.\s*\**\s*Title\b", stripped, re.IGNORECASE):
                    is_subfield = True

            if not is_subfield:
                is_new_citation = True

        if is_new_citation:
            flush_current()
            current = [stripped]
            continue

        # Normal line belonging to current citation or starting a raw metadata block
        if current:
            current.append(stripped)
        elif any(re.search(pattern, stripped, re.IGNORECASE) for pattern in [
            r"^(?:###\s*)?(?:\*\*)?Title\s*:",
            r"^(?:###\s*)?(?:\*\*)?Authors?\s*:",
            r"^(?:###\s*)?(?:\*\*)?DOI\s*:",
            r"^(?:###\s*)?(?:\*\*)?Venue\s*:",
            r"^(?:###\s*)?(?:\*\*)?arXiv\s*:"
        ]):
            current = [stripped]

    flush_current()

    # Fallback: If no citations extracted, check if the input text itself is a single citation
    if not citations and text.strip():
        stripped_text = text.strip()
        if is_valid_citation(stripped_text):
            citations = [stripped_text]

    # Filter invalid blocks: only keep genuine citations
    valid = [c for c in citations if is_valid_citation(c)]

    # Remove duplicates preserving order
    unique = []
    seen = set()
    for citation in valid:
        if citation not in seen:
            seen.add(citation)
            unique.append(citation)

    return unique