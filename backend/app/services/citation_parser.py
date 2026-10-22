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
        result["doi"] = doi.group().strip().rstrip(".,;:)]}")

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
        raw_title = title.group(1).strip()
        # Strip trailing metadata if Title line had multiple fields
        raw_title = re.split(r"\s+(?:Authors?|Venue|Conference|Year|DOI|arXiv):", raw_title, flags=re.IGNORECASE)[0]
        raw_title = raw_title.strip("\"'“”., ")
        result["title"] = raw_title

    else:

        quoted = re.search(
            r'["“\']([^"”\']+)["”\']',
            citation,
        )

        if quoted:

            result["title"] = quoted.group(1).strip()

        else:
            # Fallback: Assume the title is on the first line
            first_line = citation.split("\n")[0]
            # Strip standard prefix formats like '1. ' or '[1] '
            title_match = re.sub(r"^(\d+\.|\[\d+\]|###\s*Paper\s*\d+:?)\s*", "", first_line).strip()

            # Remove Markdown bold formatting if present
            title_match = title_match.replace("**", "").strip("\"'“” ")

            if title_match and len(title_match) > 5:
                if not title_match.lower().startswith("author") and not title_match.lower().startswith("paper"):
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
        r"\n|Year:|Venue:|Conference:|Journal:|Booktitle:|DOI:|arXiv:|published\s+in|published|in\s+(?:19|20)\d{2}",
        author_text,
        flags=re.IGNORECASE,
    )[0]

    author_text = author_text.replace("et al.", "").replace("et al", "").strip()

    if ";" in author_text:
        authors = [a.strip() for a in author_text.split(";") if a.strip()]
    else:
        chunks = re.split(r"\s+(?:and|&)\s+", author_text)
        authors = []
        for chunk in chunks:
            matches = list(re.finditer(r"([A-Z][a-zA-Z\s\'-]+?),\s*([A-Z](?:\.[A-Z])*\.?(?:\s+[A-Z]\.?)*)(?=,|$)", chunk))
            if len(matches) > 1 or (len(matches) == 1 and matches[0].group().strip() == chunk.strip()):
                for m in matches:
                    authors.append(m.group().strip())
            else:
                for part in chunk.split(","):
                    part = part.strip()
                    if part:
                        authors.append(part)

    result["authors"] = [
        a.strip(" .\"'")
        for a in authors
        if a.strip(" .\"'") and not re.match(r"^(?:published|in|\d{4})$", a.strip(" .\"'"), re.IGNORECASE)
    ]

    # -------------------------------------------------------
    # VENUE
    # -------------------------------------------------------

    venue = re.search(
        r'(?:Venue|Conference|Journal|Booktitle|Published in)\s*:\s*(.+)',
        citation,
        re.IGNORECASE,
    )

    if venue:

        v = venue.group(1).strip()
        # Clean trailing year like ", 2016" or "(2016)"
        v = re.sub(r"[\s,\(]+(19|20)\d{2}[\)]*$", "", v).strip()
        # Strip leading numbering like "3. "
        v = re.sub(r"^\d+\.\s*", "", v).strip()
        result["venue"] = v

    else:

        for line in citation.splitlines():

            lower = line.lower()

            if lower.startswith("doi") or lower.startswith("arxiv") or lower.startswith("title"):
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
                "iclr",
                "acm",
                "springer",
                "nature",
                "naacl",
                "acl",
                "emnlp",
            ]):

                clean_line = re.sub(r"^\d+\.\s*(?:\**Conference:\**|\**Venue:\**|\**Journal:\**)?\s*", "", line).strip()
                clean_line = re.sub(r"[\s,\(]+(19|20)\d{2}[\)]*$", "", clean_line).strip()
                result["venue"] = clean_line
                break

    return result