import re


def normalize_text(text: str):
    """
    Normalize text for comparison.
    """

    if not text:
        return ""

    text = text.lower()

    text = re.sub(r"[^a-z0-9 ]", " ", text)

    text = re.sub(r"\s+", " ", text)

    return text.strip()


def normalize_title(title: str):
    """
    Normalize paper title.
    """

    return normalize_text(title)


def normalize_author(author: str):
    """
    Normalize a single author name.
    """

    if not author:
        return ""

    author = normalize_text(author)

    # Remove titles
    author = re.sub(r"\b(dr|prof|mr|mrs|ms)\b", "", author)

    author = re.sub(r"\s+", " ", author)

    return author.strip()


def normalize_authors(authors):
    """
    Normalize list of authors.
    """

    if not authors:
        return []

    return [
        normalize_author(author)
        for author in authors
        if author
    ]


def normalize_venue(venue: str):
    """
    Normalize publication venue.
    """

    if not venue:
        return ""

    venue = normalize_text(venue)

    replacements = {
        "proceedings of": "",
        "international": "",
        "conference on": "",
        "ieee": "",
        "acm": "",
        "journal of": "",
        "transactions on": "",
        "the": "",
    }

    for old, new in replacements.items():
        venue = venue.replace(old, new)

    venue = re.sub(r"\s+", " ", venue)

    return venue.strip()


def normalize_doi(doi: str):
    """
    Normalize DOI:
    - remove "https://doi.org/"
    - remove "http://doi.org/"
    - remove "doi:"
    - trim whitespace
    - remove trailing punctuation
    - normalize case
    """
    if not doi:
        return None

    d = str(doi).strip()
    d = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", d, flags=re.IGNORECASE)
    d = re.sub(r"^doi:\s*", "", d, flags=re.IGNORECASE)
    d = d.strip().rstrip(".,;:)]}")
    m = re.search(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+", d)
    if m:
        d = m.group().rstrip(".,;:)]}")
    return d.lower()


def normalize_metadata(metadata: dict):
    """
    Normalize an entire metadata dictionary.
    """

    if metadata is None:
        return None

    return {
        "title": normalize_title(metadata.get("title")),
        "authors": normalize_authors(metadata.get("authors", [])),
        "venue": normalize_venue(metadata.get("venue")),
        "year": metadata.get("year"),
        "doi": normalize_doi(metadata.get("doi")),
    }


def canonicalize_verified_metadata(paper: dict, parsed_citation: dict = None) -> dict:
    """
    Produce canonical, clean verified metadata for Suggested Citation generation.
    Ensures a single canonical verified publication year without duplicates or conflicts.
    """
    if not paper:
        return None

    # 1. Title
    title = str(paper.get("title") or "").strip().strip("\"'“”")
    title = re.sub(r"\s+", " ", title)

    # 2. Authors
    raw_authors = paper.get("authors") or []
    if isinstance(raw_authors, str):
        raw_authors = [a.strip() for a in raw_authors.split(";") if a.strip()]
    cleaned_authors = []
    for a in raw_authors:
        a_clean = str(a).strip().strip("\"'“”.,")
        if a_clean:
            cleaned_authors.append(a_clean)

    # If parsed_citation has fuller matching author names (e.g. "Aaron Courville" vs "A. Courville"), preserve full names
    if parsed_citation and parsed_citation.get("authors"):
        from app.services.similarity_service import compare_authors
        parsed_authors = parsed_citation["authors"]
        if len(parsed_authors) == len(cleaned_authors) and compare_authors(parsed_authors, cleaned_authors) >= 80:
            def _count_initials(names):
                return sum(1 for n in names if n.split() and re.match(r"^[A-Z]\.?$", n.split()[0]))
            if _count_initials(cleaned_authors) > _count_initials(parsed_authors):
                cleaned_authors = parsed_authors

    # 3. Canonical Publication Year
    raw_venue = str(paper.get("venue") or "").strip()
    venue_year_match = re.search(r"\b((?:19|20)\d{2})\b", raw_venue)
    venue_year = int(venue_year_match.group(1)) if venue_year_match else None

    paper_year = paper.get("year")
    try:
        paper_year = int(paper_year) if paper_year else None
    except (ValueError, TypeError):
        paper_year = None

    alt_years = [int(y) for y in paper.get("alternate_years", []) if str(y).isdigit()]
    parsed_year = None
    if parsed_citation and parsed_citation.get("year"):
        try:
            parsed_year = int(parsed_citation["year"])
        except (ValueError, TypeError):
            pass

    source = paper.get("source") or "Crossref"

    # Canonical year selection with source-priority logic:
    # 1) If venue string contains an explicit conference year matching an alternate year or parsed year,
    #    use the venue conference year (e.g. "2016 IEEE CVPR" published year 2016)
    if venue_year and (venue_year in alt_years or venue_year == parsed_year or venue_year == paper_year or raw_venue.startswith(str(venue_year))):
        canonical_year = venue_year
    elif source == "Crossref" and paper_year:
        canonical_year = paper_year
    elif parsed_year and (parsed_year in alt_years or parsed_year == paper_year):
        canonical_year = parsed_year
    elif paper_year:
        canonical_year = paper_year
    elif alt_years:
        canonical_year = max(alt_years)
    else:
        canonical_year = venue_year

    # 4. Canonical Venue - strip leading and trailing years to avoid duplication
    venue = raw_venue
    venue = re.sub(r"^(?:19|20)\d{2}\s+", "", venue).strip()
    venue = re.sub(r"[\s,\(]+(?:19|20)\d{2}[\)]*$", "", venue).strip()
    venue = venue.rstrip(".,;")

    # 5. Canonical DOI - clean prefixes and standardize publisher acronyms
    doi = str(paper.get("doi") or "").strip()
    doi = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", doi, flags=re.IGNORECASE)
    doi = re.sub(r"^doi:\s*", "", doi, flags=re.IGNORECASE)
    m = re.match(r"^(10\.1109/)([a-zA-Z]+)(\..+)$", doi)
    if m:
        doi = m.group(1) + m.group(2).upper() + m.group(3)

    return {
        "title": title,
        "authors": cleaned_authors,
        "venue": venue,
        "year": canonical_year,
        "doi": doi,
        "source": source,
    }