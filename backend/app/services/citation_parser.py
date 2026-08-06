import re


def parse_citation(citation: str):
    """
    Parse citation into structured metadata.

    Supports:
    - IEEE
    - Gemini
    - ChatGPT
    """

    result = {
        "raw": citation,
        "title": None,
        "authors": [],
        "venue": None,
        "year": None,
        "doi": None,
        "arxiv": None,
    }

    # -------------------------------------------------------
    # Clean markdown
    # -------------------------------------------------------

    citation = citation.replace("**", "").strip()

    # -------------------------------------------------------
    # DOI
    # -------------------------------------------------------

    doi = re.search(
        r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+",
        citation,
        re.IGNORECASE,
    )

    if doi:
        result["doi"] = doi.group().strip()

    # -------------------------------------------------------
    # arXiv
    # -------------------------------------------------------

    arxiv = re.search(
        r"arXiv:\d{4}\.\d{4,5}",
        citation,
        re.IGNORECASE,
    )

    if arxiv:
        result["arxiv"] = arxiv.group()

    # -------------------------------------------------------
    # YEAR
    # -------------------------------------------------------

    year = re.search(
        r"Year\s*:\s*(19|20)\d{2}",
        citation,
        re.IGNORECASE,
    )

    if year:
        result["year"] = int(re.search(r"\d{4}", year.group()).group())
    else:
        year = re.search(r"\b(19|20)\d{2}\b", citation)
        if year:
            result["year"] = int(year.group())

        # -------------------------------------------------------
    # TITLE
    # -------------------------------------------------------

    title = re.search(
        r'Title\s*:\s*(.+)',
        citation,
        re.IGNORECASE,
    )

    if title:

        result["title"] = title.group(1).strip()

    else:

        quoted = re.search(
            r'"([^"]+)"',
            citation,
        )

        if quoted:

            result["title"] = quoted.group(1).strip()
            
        else:
            # Fallback: Assume the title is on the first line
            first_line = citation.split("\n")[0]
            # Strip standard prefix formats like '1. ' or '[1] '
            title_match = re.sub(r"^(\d+\.|\[\d+\])\s*", "", first_line).strip()
            
            # Remove Markdown bold formatting if present
            title_match = title_match.replace("**", "")
            
            if title_match and len(title_match) > 5:
                if not title_match.lower().startswith("author"):
                    result["title"] = title_match

    # -------------------------------------------------------
    # AUTHORS
    # -------------------------------------------------------

    author_line = re.search(
        r'Authors?\s*:\s*(.+)',
        citation,
        re.IGNORECASE,
    )

    if author_line:

        author_text = author_line.group(1)

    else:

        by = re.search(
            r'by\s+(.+)',
            citation,
            re.IGNORECASE,
        )

        author_text = by.group(1) if by else ""

    author_text = re.split(
        r"\n|Year:|Venue:|DOI:",
        author_text,
        flags=re.IGNORECASE,
    )[0]

    author_text = author_text.replace("et al.", "")

    authors = re.split(
        r",| and ",
        author_text,
    )

    result["authors"] = [
        a.strip(" .")
        for a in authors
        if a.strip()
    ]

    # -------------------------------------------------------
    # VENUE
    # -------------------------------------------------------

    venue = re.search(
        r'Venue\s*:\s*(.+)',
        citation,
        re.IGNORECASE,
    )

    if venue:

        result["venue"] = venue.group(1).strip()

    else:

        for line in citation.splitlines():

            lower = line.lower()

            if lower.startswith("doi"):
                continue

            if any(k in lower for k in [
                "ieee",
                "conference",
                "transactions",
                "journal",
                "cvpr",
                "iccv",
                "eccv",
                "neurips",
                "nips",
                "icml",
                "acm",
                "springer",
                "nature",
            ]):

                result["venue"] = line.strip()
                break

    return result