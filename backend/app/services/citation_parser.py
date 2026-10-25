import re


def parse_citation(citation: str):
    """
    Parse citation into structured metadata.

    Supports:
    - IEEE (e.g. A. Vaswani et al., "Title," in Venue, 2017, pp. ...)
    - Gemini / ChatGPT / LLM formats
    - Labeled benchmark formats (Title: ..., Authors: ..., Year: ..., Venue: ..., DOI: ...)
    - Free-text academic citations
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
        result["arxiv"] = arxiv.group().strip().rstrip(".,;:)]}")

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

    quoted_match = None
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
            quoted_match = quoted
            result["title"] = quoted.group(1).strip(" \t\n\"'“”.,")

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

        if by:
            author_text = by.group(1)
        elif quoted_match:
            # Free-text / IEEE format where authors precede the quoted title
            pre_title = citation[:quoted_match.start()].strip()
            # Remove leading citation identifiers like [1], 1., etc.
            pre_title = re.sub(r"^(\d+\.|\[\d+\]|###\s*Paper\s*\d+:?)\s*", "", pre_title).strip()
            # Strip conversational introductory clauses like "Here is the paper: ", "Reference: "
            pre_title = re.sub(r"^(?:Here\s+is\s+(?:the\s+)?(?:paper|reference|citation)[^:]*:\s*|See[:\s]*|Reference[:\s]*)+", "", pre_title, flags=re.IGNORECASE).strip()
            # Ignore if pre_title is just a field header or empty
            if pre_title and not re.match(r"^(?:Title|Paper|Ref|Reference)\b", pre_title, re.IGNORECASE):
                author_text = pre_title
            else:
                author_text = ""
        else:
            author_text = ""

    author_text = re.split(
        r"\n|Year:|Venue:|Conference:|Journal:|Booktitle:|DOI:|arXiv:|published\s+in|published|in\s+(?:19|20)\d{2}",
        author_text,
        flags=re.IGNORECASE,
    )[0]

    author_text = author_text.replace("et al.", "").replace("et al", "").strip().rstrip(",")

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

    elif quoted_match:
        # In free-text / IEEE format, venue typically follows the quoted title, preceded by 'in ' or ','
        post_title = citation[quoted_match.end():]
        venue_match = re.search(
            r'(?:,\s*in\s+|\s+in\s+|[,]\s*)([A-Za-z0-9\s:&\-\.]+?)(?:,\s*(?:19|20)\d{2}|,\s*(?:vol|pp|pages|\d{4})|\.\s*(?:doi|arXiv)|,\s*(?:doi|arXiv)|$)',
            post_title,
            re.IGNORECASE,
        )
        if venue_match:
            clean_v = venue_match.group(1).strip(" \t\n,.")
            clean_v = re.sub(r"[\s,\(]+(19|20)\d{2}[\)]*$", "", clean_v).strip()
            if clean_v and len(clean_v) > 2 and not clean_v.lower().startswith("doi"):
                result["venue"] = clean_v

    if not result["venue"]:

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
