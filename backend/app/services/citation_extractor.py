import re

def extract_citations(text: str):
    """
    Extract citations from LLM responses.

    Supports:
    1. IEEE references
       [1] ...
    2. GPT/Gemini numbered format
    3. OpenAI format

    The extractor works line-by-line instead of relying on
    large regexes, making it much more reliable.
    """

    text = text.replace("\r\n", "\n")
    lines = text.split("\n")
    citations = []
    current = []

    # Match 1. but NOT if followed by Title, Authors, Conference, etc.
    numbered_pattern = re.compile(r"^\d+\.(?!\s*\**\s*(?:Title|Authors?|Venue|Conference|Year|DOI|Abstract|Summary|Key Contribution|Link|Publication)\b)\s*", re.IGNORECASE)
    ieee_pattern = re.compile(r"^\[\d+\]")
    paper_pattern = re.compile(r"^(?:###\s*)?(?:\*\*)?Paper\s*\d+", re.IGNORECASE)

    for line in lines:
        stripped = line.strip()

        if not stripped:
            continue

        # -------------------------------------------------
        # New citation starts (Numbered, IEEE, or 'Paper X')
        # -------------------------------------------------
        if paper_pattern.match(stripped) or numbered_pattern.match(stripped) or ieee_pattern.match(stripped):
            if current:
                citations.append("\n".join(current).strip())
            current = [stripped]
            continue

        # -------------------------------------------------
        # Normal line belonging to current citation
        # -------------------------------------------------
        if current:
            current.append(stripped)

    # append last citation
    if current:
        citations.append("\n".join(current).strip())

    # -------------------------------------------------
    # Filter invalid blocks
    # -------------------------------------------------
    valid = []
    for citation in citations:
        lower = citation.lower()
        if (
            '"' in citation
            or "title:" in lower
            or "doi:" in lower
            or "authors:" in lower
        ):
            valid.append(citation)

    # -------------------------------------------------
    # Remove duplicates
    # -------------------------------------------------
    unique = []
    seen = set()
    for citation in valid:
        if citation not in seen:
            seen.add(citation)
            unique.append(citation)

    return unique